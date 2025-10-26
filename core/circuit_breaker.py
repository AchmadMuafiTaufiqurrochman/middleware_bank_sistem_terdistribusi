# Circuit Breaker Pattern Implementation
from datetime import datetime, timedelta
from typing import Dict, Optional
import asyncio
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """
    Circuit Breaker untuk melindungi sistem dari cascading failures
    ketika berkomunikasi dengan external services
    """
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # seconds
        self.circuits: Dict[str, Dict] = {}
        
    def _get_circuit(self, service_name: str) -> Dict:
        """Get or create circuit for service"""
        if service_name not in self.circuits:
            self.circuits[service_name] = {
                'state': CircuitState.CLOSED,
                'failure_count': 0,
                'last_failure_time': None,
                'success_count': 0
            }
        return self.circuits[service_name]
    
    async def call(self, service_name: str, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection
        
        Args:
            service_name: Unique identifier for the service
            func: Async function to execute
            *args, **kwargs: Arguments to pass to function
        """
        circuit = self._get_circuit(service_name)
        
        # Check circuit state
        if circuit['state'] == CircuitState.OPEN:
            if circuit['last_failure_time']:
                time_since_failure = (datetime.now() - circuit['last_failure_time']).total_seconds()
                if time_since_failure > self.timeout:
                    # Try half-open
                    circuit['state'] = CircuitState.HALF_OPEN
                    circuit['success_count'] = 0
                else:
                    raise Exception(f"Circuit breaker OPEN for {service_name}. Service unavailable.")
        
        try:
            # Execute function
            result = await func(*args, **kwargs)
            
            # Success - reset or close circuit
            if circuit['state'] == CircuitState.HALF_OPEN:
                circuit['success_count'] += 1
                if circuit['success_count'] >= 2:  # Need 2 successes to close
                    circuit['state'] = CircuitState.CLOSED
                    circuit['failure_count'] = 0
            elif circuit['state'] == CircuitState.CLOSED:
                circuit['failure_count'] = 0
            
            return result
            
        except Exception as e:
            # Failure - increment counter
            circuit['failure_count'] += 1
            circuit['last_failure_time'] = datetime.now()
            
            # Open circuit if threshold reached
            if circuit['failure_count'] >= self.failure_threshold:
                circuit['state'] = CircuitState.OPEN
            
            raise e
    
    def get_state(self, service_name: str) -> CircuitState:
        """Get current state of circuit"""
        circuit = self._get_circuit(service_name)
        return circuit['state']
    
    def reset(self, service_name: str):
        """Manually reset circuit"""
        if service_name in self.circuits:
            self.circuits[service_name] = {
                'state': CircuitState.CLOSED,
                'failure_count': 0,
                'last_failure_time': None,
                'success_count': 0
            }

# Global circuit breaker instance
circuit_breaker = CircuitBreaker()
