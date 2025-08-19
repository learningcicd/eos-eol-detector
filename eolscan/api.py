"""
FastAPI Web Service for EOL/EOS Scanner
Provides REST endpoints and MCP-like functionality for production deployment
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from .cli import scan_repo, scan_path
from .risk_model import assess_risk, get_risk_model
from .util import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)

# Pydantic models
class ScanRequest(BaseModel):
    """Request model for scanning"""
    repo: Optional[str] = Field(None, description="GitHub repo in format owner/name")
    path: Optional[str] = Field(None, description="Local path to scan")
    sbom_path: Optional[str] = Field(None, description="Path to local SBOM file")
    ref: Optional[str] = Field(None, description="Git branch/ref to scan")
    near_months: int = Field(6, description="Months threshold for 'Near EOL' classification")
    include_risk_assessment: bool = Field(True, description="Include ML risk assessment")

class ScanResponse(BaseModel):
    """Response model for scan results"""
    scan_id: str
    timestamp: str
    results: List[Dict[str, Any]]
    summary: Dict[str, Any]
    risk_assessment: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any]

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str
    model_status: str

class ModelInfoResponse(BaseModel):
    """Model information response"""
    model_type: str
    features: List[str]
    last_trained: Optional[str]
    accuracy: Optional[float]

# Initialize FastAPI app
app = FastAPI(
    title="EOL/EOS Scanner API",
    description="Production-ready API for detecting EOL/EOS risks with ML-powered risk assessment",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
SCAN_HISTORY = {}  # In production, use a proper database
MAX_SCAN_HISTORY = 1000

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify API token"""
    token = credentials.credentials
    expected_token = os.getenv("API_TOKEN")
    
    if not expected_token:
        logger.warning("No API_TOKEN configured, allowing all requests")
        return token
    
    if token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token"
        )
    
    return token

def verify_token_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """Verify API token (optional - for endpoints that can work without auth)"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return verify_token(credentials)

def generate_scan_id() -> str:
    """Generate unique scan ID"""
    return f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"

def create_summary(results: List[Dict]) -> Dict[str, Any]:
    """Create summary statistics from scan results"""
    total_items = len(results)
    eol_count = sum(1 for r in results if r.get('status') == 'EOL')
    near_eol_count = sum(1 for r in results if r.get('status') == 'Near EOL')
    supported_count = sum(1 for r in results if r.get('status') == 'Supported')
    unknown_count = sum(1 for r in results if r.get('status') == 'Unknown')
    
    # Risk level distribution
    risk_levels = {}
    for r in results:
        risk_level = r.get('risk_level', 'UNKNOWN')
        risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
    
    return {
        "total_items": total_items,
        "eol_count": eol_count,
        "near_eol_count": near_eol_count,
        "supported_count": supported_count,
        "unknown_count": unknown_count,
        "risk_levels": risk_levels,
        "critical_risks": risk_levels.get('CRITICAL', 0),
        "high_risks": risk_levels.get('HIGH', 0)
    }

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "EOL/EOS Scanner API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    model_status = "available"
    try:
        model = get_risk_model()
        if model.model is None:
            model_status = "rule_based_fallback"
    except Exception as e:
        model_status = f"error: {str(e)}"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        model_status=model_status
    )

@app.get("/model/info", response_model=ModelInfoResponse)
async def model_info():
    """Get information about the risk model"""
    try:
        model = get_risk_model()
        
        # Check if model is properly initialized
        model_type = "RandomForest"
        if model.model is None:
            model_type = "RuleBased"
        elif not hasattr(model.model, 'estimators_') or not model.model.estimators_:
            model_type = "RuleBased"
        
        return ModelInfoResponse(
            model_type=model_type,
            features=model.feature_names,
            last_trained=None,  # Would track in production
            accuracy=None  # Would track in production
        )
    except Exception as e:
        logger.error(f"Error in model info endpoint: {e}")
        # Return fallback response
        return ModelInfoResponse(
            model_type="RuleBased",
            features=[
                'days_to_eol', 'days_since_last_release', 'release_frequency',
                'advisory_count', 'security_advisory_count', 'dependency_count',
                'ecosystem_popularity', 'maintainer_count'
            ],
            last_trained=None,
            accuracy=None
        )

@app.post("/scan", response_model=ScanResponse)
async def scan_endpoint(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """
    Main scanning endpoint - supports both repo and path scanning
    """
    scan_id = generate_scan_id()
    start_time = datetime.now()
    
    try:
        # Validate request
        if not request.repo and not request.path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'repo' or 'path' must be provided"
            )
        
        # Get GitHub token from environment
        github_token = os.getenv("GITHUB_TOKEN")
        
        # Perform scan with timeout handling
        try:
            if request.repo:
                logger.info(f"Scanning repo: {request.repo}")
                results = scan_repo(
                    owner_repo=request.repo,
                    ref=request.ref,
                    token=github_token,
                    near_months=request.near_months
                )
            else:
                logger.info(f"Scanning path: {request.path}")
                results = scan_path(
                    path=Path(request.path),
                    near_months=request.near_months,
                    sbom_path=request.sbom_path
                )
        except Exception as scan_error:
            logger.error(f"Scan operation failed: {scan_error}")
            # Return partial results or error message
            results = [{
                "type": "error",
                "message": f"Scan failed: {str(scan_error)}",
                "target": request.repo or request.path
            }]
        
        # Add risk assessment if requested
        if request.include_risk_assessment and results:
            enhanced_results = []
            for result in results:
                if result.get('type') in ['runtime', 'package']:
                    try:
                        enhanced_result = assess_risk(result)
                        enhanced_results.append(enhanced_result)
                    except Exception as risk_error:
                        logger.warning(f"Risk assessment failed for {result.get('name', 'unknown')}: {risk_error}")
                        enhanced_results.append(result)
                else:
                    enhanced_results.append(result)
            results = enhanced_results
        
        # Create summary
        summary = create_summary(results)
        
        # Prepare response
        response = ScanResponse(
            scan_id=scan_id,
            timestamp=start_time.isoformat(),
            results=results,
            summary=summary,
            metadata={
                "scan_type": "repo" if request.repo else "path",
                "target": request.repo or request.path,
                "near_months": request.near_months,
                "risk_assessment_included": request.include_risk_assessment,
                "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
            }
        )
        
        # Store in history (in production, use database)
        SCAN_HISTORY[scan_id] = {
            "request": request.dict(),
            "response": response.dict(),
            "timestamp": start_time.isoformat()
        }
        
        # Cleanup old history
        if len(SCAN_HISTORY) > MAX_SCAN_HISTORY:
            oldest_keys = sorted(SCAN_HISTORY.keys())[:len(SCAN_HISTORY) - MAX_SCAN_HISTORY]
            for key in oldest_keys:
                del SCAN_HISTORY[key]
        
        return response
        
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan failed: {str(e)}"
        )

@app.get("/scan/{scan_id}", response_model=Dict[str, Any])
async def get_scan_result(
    scan_id: str,
    token: str = Depends(verify_token)
):
    """Get scan result by ID"""
    if scan_id not in SCAN_HISTORY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    return SCAN_HISTORY[scan_id]

@app.get("/scan", response_model=Dict[str, Any])
async def get_scan_status(
    token: str = Depends(verify_token_optional)
):
    """Get scan status and recent scans"""
    recent_scans = list(SCAN_HISTORY.values())[-5:]  # Last 5 scans
    return {
        "total_scans": len(SCAN_HISTORY),
        "recent_scans": recent_scans,
        "message": "Use POST /scan to perform new scans"
    }

@app.get("/scans", response_model=List[Dict[str, Any]])
async def list_scans(
    limit: int = 10,
    token: str = Depends(verify_token)
):
    """List recent scans"""
    scans = list(SCAN_HISTORY.values())
    scans.sort(key=lambda x: x['timestamp'], reverse=True)
    return scans[:limit]

@app.post("/scan/batch")
async def batch_scan(
    requests: List[ScanRequest],
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Batch scan multiple targets"""
    if len(requests) > 10:  # Limit batch size
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size cannot exceed 10"
        )
    
    results = []
    for i, request in enumerate(requests):
        try:
            # Create a temporary scan ID for batch
            scan_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"
            
            # Perform scan with timeout handling
            try:
                if request.repo:
                    scan_results = scan_repo(
                        owner_repo=request.repo,
                        ref=request.ref,
                        token=os.getenv("GITHUB_TOKEN"),
                        near_months=request.near_months
                    )
                else:
                    scan_results = scan_path(
                        path=Path(request.path),
                        near_months=request.near_months,
                        sbom_path=request.sbom_path
                    )
            except Exception as scan_error:
                scan_results = [{
                    "type": "error",
                    "message": f"Scan failed: {str(scan_error)}",
                    "target": request.repo or request.path
                }]
            
            # Add risk assessment
            if request.include_risk_assessment and scan_results:
                enhanced_results = []
                for result in scan_results:
                    if result.get('type') in ['runtime', 'package']:
                        try:
                            enhanced_result = assess_risk(result)
                            enhanced_results.append(enhanced_result)
                        except Exception as risk_error:
                            logger.warning(f"Risk assessment failed for {result.get('name', 'unknown')}: {risk_error}")
                            enhanced_results.append(result)
                    else:
                        enhanced_results.append(result)
                scan_results = enhanced_results
            
            results.append({
                "scan_id": scan_id,
                "request": request.dict(),
                "results": scan_results,
                "summary": create_summary(scan_results),
                "status": "success"
            })
            
        except Exception as e:
            results.append({
                "scan_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                "request": request.dict(),
                "error": str(e),
                "status": "failed"
            })
    
    return {
        "batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "total_requests": len(requests),
        "successful": sum(1 for r in results if r['status'] == 'success'),
        "failed": sum(1 for r in results if r['status'] == 'failed'),
        "results": results
    }

@app.post("/model/train")
async def train_model(
    training_data: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Train the risk model with new data"""
    try:
        if not training_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No training data provided"
            )
        
        model = get_risk_model()
        
        # Validate training data format
        validated_data = []
        for item in training_data:
            if 'features' in item and 'risk_label' in item:
                validated_data.append(item)
            else:
                logger.warning(f"Skipping invalid training item: {item}")
        
        if len(validated_data) < 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient training data. Need at least 5 samples, got {len(validated_data)}"
            )
        
        # Run training in background to avoid timeout
        try:
            background_tasks.add_task(model.train, validated_data)
            
            return {
                "status": "success",
                "message": "Model training started",
                "training_samples": len(validated_data),
                "model_type": "RandomForest"
            }
        except Exception as train_error:
            logger.error(f"Failed to start model training: {train_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start model training: {str(train_error)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model training failed: {str(e)}"
        )

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the FastAPI server"""
    uvicorn.run(
        "eolscan.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    run_server()
