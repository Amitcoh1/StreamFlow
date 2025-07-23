"""
StreamFlow Kubernetes Mutating Webhook
Automatically enhances deployed services with StreamFlow monitoring capabilities
"""
import json
import base64
import logging
import os
from typing import Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="StreamFlow Mutating Webhook",
    description="Automatically enhances Kubernetes deployments with StreamFlow monitoring",
    version="1.0.0"
)

class AdmissionRequest(BaseModel):
    """Kubernetes AdmissionRequest structure"""
    uid: str
    kind: Dict[str, str]
    resource: Dict[str, str]
    object: Dict[str, Any]
    operation: str

class AdmissionReview(BaseModel):
    """Kubernetes AdmissionReview structure"""
    apiVersion: str
    kind: str
    request: AdmissionRequest

class StreamFlowWebhook:
    """StreamFlow Kubernetes Mutating Webhook"""
    
    def __init__(self):
        self.streamflow_annotations = {
            "streamflow.io/monitoring": "enabled",
            "streamflow.io/metrics-path": "/metrics",
            "streamflow.io/metrics-port": "8080",
            "streamflow.io/health-path": "/health",
            "streamflow.io/version": "1.0.0",
            "streamflow.io/injected-at": ""
        }
        
        self.streamflow_labels = {
            "streamflow.io/managed": "true",
            "streamflow.io/component": "microservice"
        }
    
    def should_mutate(self, obj: Dict[str, Any]) -> bool:
        """Determine if object should be mutated"""
        # Only mutate Deployments and Services
        kind = obj.get("kind", "")
        if kind not in ["Deployment", "Service"]:
            return False
        
        # Skip if already has StreamFlow annotations
        annotations = obj.get("metadata", {}).get("annotations", {})
        if "streamflow.io/monitoring" in annotations:
            logger.info("Object already has StreamFlow annotations, skipping")
            return False
        
        # Skip system namespaces
        namespace = obj.get("metadata", {}).get("namespace", "default")
        if namespace in ["kube-system", "kube-public", "kube-node-lease", "streamflow-webhook"]:
            return False
        
        return True
    
    def create_patches(self, obj: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create JSON patches to add StreamFlow monitoring"""
        patches = []
        
        # Add timestamp
        current_time = datetime.now().isoformat()
        self.streamflow_annotations["streamflow.io/injected-at"] = current_time
        
        # Ensure metadata exists
        if "metadata" not in obj:
            patches.append({
                "op": "add",
                "path": "/metadata",
                "value": {}
            })
        
        # Add annotations
        if "annotations" not in obj.get("metadata", {}):
            patches.append({
                "op": "add",
                "path": "/metadata/annotations",
                "value": self.streamflow_annotations
            })
        else:
            # Add individual annotations
            for key, value in self.streamflow_annotations.items():
                patches.append({
                    "op": "add",
                    "path": f"/metadata/annotations/{key.replace('/', '~1')}",
                    "value": value
                })
        
        # Add labels
        if "labels" not in obj.get("metadata", {}):
            patches.append({
                "op": "add",
                "path": "/metadata/labels",
                "value": self.streamflow_labels
            })
        else:
            # Add individual labels
            for key, value in self.streamflow_labels.items():
                patches.append({
                    "op": "add",
                    "path": f"/metadata/labels/{key.replace('/', '~1')}",
                    "value": value
                })
        
        # For Deployments, also add to pod template
        if obj.get("kind") == "Deployment":
            patches.extend(self._add_pod_template_patches(obj))
        
        return patches
    
    def _add_pod_template_patches(self, obj: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Add StreamFlow annotations to pod template"""
        patches = []
        
        # Add annotations to pod template
        template_path = "/spec/template/metadata/annotations"
        if not obj.get("spec", {}).get("template", {}).get("metadata", {}).get("annotations"):
            patches.append({
                "op": "add",
                "path": template_path,
                "value": self.streamflow_annotations
            })
        else:
            for key, value in self.streamflow_annotations.items():
                patches.append({
                    "op": "add",
                    "path": f"{template_path}/{key.replace('/', '~1')}",
                    "value": value
                })
        
        # Add labels to pod template  
        template_labels_path = "/spec/template/metadata/labels"
        if not obj.get("spec", {}).get("template", {}).get("metadata", {}).get("labels"):
            patches.append({
                "op": "add",
                "path": template_labels_path,
                "value": self.streamflow_labels
            })
        else:
            for key, value in self.streamflow_labels.items():
                patches.append({
                    "op": "add",
                    "path": f"{template_labels_path}/{key.replace('/', '~1')}",
                    "value": value
                })
        
        return patches

# Global webhook instance
webhook = StreamFlowWebhook()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "streamflow-webhook"}

@app.post("/mutate")
async def mutate(request: Request):
    """Main mutating webhook endpoint"""
    try:
        # Parse admission review
        body = await request.json()
        logger.info(f"Received admission review: {body.get('request', {}).get('uid', 'unknown')}")
        
        admission_review = AdmissionReview(**body)
        req = admission_review.request
        
        # Check if we should mutate this object
        if not webhook.should_mutate(req.object):
            logger.info(f"Skipping mutation for {req.kind}/{req.object.get('metadata', {}).get('name', 'unknown')}")
            return create_admission_response(req.uid, allowed=True)
        
        # Create patches
        patches = webhook.create_patches(req.object)
        logger.info(f"Created {len(patches)} patches for {req.kind}/{req.object.get('metadata', {}).get('name', 'unknown')}")
        
        # Create response with patches
        if patches:
            patch_bytes = json.dumps(patches).encode('utf-8')
            patch_b64 = base64.b64encode(patch_bytes).decode('utf-8')
            
            return create_admission_response(
                req.uid, 
                allowed=True, 
                patch=patch_b64,
                patch_type="JSONPatch"
            )
        else:
            return create_admission_response(req.uid, allowed=True)
            
    except Exception as e:
        logger.error(f"Error processing admission review: {e}")
        return create_admission_response("unknown", allowed=False, message=str(e))

def create_admission_response(uid: str, allowed: bool = True, patch: str = None, patch_type: str = None, message: str = None):
    """Create AdmissionResponse"""
    response = {
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        "response": {
            "uid": uid,
            "allowed": allowed
        }
    }
    
    if patch:
        response["response"]["patchType"] = patch_type
        response["response"]["patch"] = patch
    
    if message:
        response["response"]["status"] = {"message": message}
    
    return JSONResponse(content=response)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "StreamFlow Mutating Webhook",
        "version": "1.0.0",
        "description": "Automatically enhances Kubernetes deployments with StreamFlow monitoring",
        "endpoints": {
            "/mutate": "Mutating webhook endpoint",
            "/health": "Health check",
            "/metrics": "Prometheus metrics (if enabled)"
        }
    }

def main():
    """Main entry point"""
    # Get configuration from environment
    port = int(os.getenv("WEBHOOK_PORT", "8443"))
    cert_dir = os.getenv("WEBHOOK_CERT_DIR", "/etc/certs")
    
    ssl_keyfile = os.path.join(cert_dir, "tls.key")
    ssl_certfile = os.path.join(cert_dir, "tls.crt")
    
    logger.info(f"Starting StreamFlow webhook on port {port}")
    logger.info(f"Using certificates from {cert_dir}")
    
    uvicorn.run(
        app,  # Use the app object directly instead of module string
        host="0.0.0.0",
        port=port,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        log_level="info"
    )

if __name__ == "__main__":
    main() 