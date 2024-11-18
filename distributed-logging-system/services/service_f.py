# services/service_f.py

from flask import Flask, jsonify, request
from base_service import BaseService
import logging
from datetime import datetime
import time
import random
import uuid
from typing import Dict, Any, Tuple
from opentelemetry.trace import Status, StatusCode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceF(BaseService):
    def __init__(self):
        super().__init__(
            service_name="ServiceF",
            port=5005,
            dependencies=[]
        )
        self.response_threshold_ms = 1000

    def process_request(self, trace_id: str = None) -> Tuple[bool, Dict[str, Any]]:
        """Process request with enhanced tracing and error handling"""
        trace_id = trace_id or str(uuid.uuid4())
        
        with self.logger.start_span("process_request", {
            "request.trace_id": trace_id
        }) as span:
            try:
                start_time = time.time()
                
                self.logger.info(
                    "Starting request processing",
                    trace_id=trace_id
                )
                
                # Simulate processing with tracing
                with self.logger.start_span("processing_operation") as proc_span:
                    processing_time = random.uniform(0.1, 2.0)
                    time.sleep(processing_time)
                    
                    total_time_ms = int((time.time() - start_time) * 1000)
                    proc_span.set_attribute("processing.time_ms", total_time_ms)
                    
                    if total_time_ms > self.response_threshold_ms:
                        proc_span.set_attribute("performance.threshold_exceeded", True)
                        self.logger.warn(
                            "Operation took longer than expected",
                            response_time_ms=total_time_ms,
                            threshold_limit_ms=self.response_threshold_ms,
                            trace_id=trace_id
                        )

                    # Simulate failures
                    if random.random() < 0.3:
                        error_scenarios = [
                            ("F_ERR_001", "Database unavailable"),
                            ("F_ERR_002", "Cache failure"),
                            ("F_ERR_003", "Resource exhausted")
                        ]
                        error_code, error_message = random.choice(error_scenarios)
                        
                        proc_span.set_status(Status(StatusCode.ERROR))
                        proc_span.set_attribute("error.code", error_code)
                        
                        self.logger.error(
                            "Operation failed",
                            error_code=error_code,
                            error_message=error_message,
                            trace_id=trace_id
                        )
                        return False, {
                            'trace_id': trace_id,
                            'error': error_code,
                            'error_message': error_message,
                            'processing_time_ms': total_time_ms
                        }

                # Success case
                self.logger.info(
                    "Successfully completed processing",
                    trace_id=trace_id,
                    processing_time_ms=total_time_ms
                )
                
                return True, {
                    'trace_id': trace_id,
                    'message': 'Processing completed successfully',
                    'processing_time_ms': total_time_ms
                }

            except Exception as e:
                span.set_status(Status(StatusCode.ERROR))
                span.record_exception(e)
                
                self.logger.error(
                    "Unexpected error in processing",
                    error_code="F_FATAL",
                    error_message=str(e),
                    trace_id=trace_id
                )
                
                return False, {
                    'trace_id': trace_id,
                    'error': 'F_FATAL',
                    'error_message': str(e)
                }

def create_app():
    app = Flask(__name__)
    service = ServiceF()
    
    @app.route('/process', methods=['GET'])
    def process():
        try:
            trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4()))
            success, result = service.process_request(trace_id)
            
            response_data = {
                'status': 'success' if success else 'error',
                'service': 'ServiceF',
                'timestamp': datetime.utcnow().isoformat(),
                'trace_id': trace_id,
                **result
            }
            
            # Add processing time to headers if available
            response = jsonify(response_data)
            if 'processing_time_ms' in result:
                response.headers['X-Processing-Time'] = str(result['processing_time_ms'])
            
            return response, 200 if success else 500
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'service': 'ServiceF',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }), 500

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            'service': 'ServiceF',
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'metrics': {
                'response_threshold_ms': service.response_threshold_ms
            }
        })

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5005)