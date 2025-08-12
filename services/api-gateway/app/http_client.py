import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.util import Timeout
import logging
from typing import Optional, Dict, Any
import time
import random

logger = logging.getLogger(__name__)

class RobustHTTPClient:
    """
    Robust HTTP client with retries, timeouts, and connection pooling
    """
    
    def __init__(self, 
                 max_retries: int = 3,
                 backoff_factor: float = 0.3,
                 connect_timeout: float = 0.5,
                 read_timeout: float = 3.0,
                 total_timeout: float = 5.0):
        
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.total_timeout = total_timeout
        
        # Create session with connection pooling
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"],
            backoff_factor=backoff_factor,
            raise_on_status=False
        )
        
        # Configure adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20,
            pool_block=False
        )
        
        # Mount adapter for both HTTP and HTTPS
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Configure keep-alive
        self.session.headers.update({
            'Connection': 'keep-alive',
            'Keep-Alive': 'timeout=65, max=1000'
        })
    
    def post_with_retry(self, 
                        url: str, 
                        data: Optional[bytes] = None,
                        json: Optional[Dict[str, Any]] = None,
                        headers: Optional[Dict[str, str]] = None,
                        timeout: Optional[float] = None) -> requests.Response:
        """
        POST request with exponential backoff retry logic
        """
        if timeout is None:
            timeout = (self.connect_timeout, self.read_timeout)
        
        attempt = 0
        last_exception = None
        
        while attempt < self.max_retries:
            try:
                start_time = time.time()
                
                response = self.session.post(
                    url=url,
                    data=data,
                    json=json,
                    headers=headers,
                    timeout=timeout
                )
                
                # Check if we should retry based on status code
                if response.status_code in [500, 502, 503, 504]:
                    raise requests.exceptions.HTTPError(f"HTTP {response.status_code}")
                
                # Success - return response
                elapsed = time.time() - start_time
                logger.info(f"HTTP request successful to {url} in {elapsed:.3f}s")
                return response
                
            except (requests.exceptions.ConnectionError, 
                    requests.exceptions.Timeout,
                    requests.exceptions.HTTPError) as e:
                
                attempt += 1
                last_exception = e
                
                if attempt >= self.max_retries:
                    logger.error(f"Final attempt failed for {url}: {e}")
                    break
                
                # Calculate backoff with jitter
                backoff_time = self.backoff_factor * (2 ** (attempt - 1))
                jitter = random.uniform(0, 0.1 * backoff_time)
                sleep_time = backoff_time + jitter
                
                logger.warning(f"Attempt {attempt} failed for {url}: {e}. "
                             f"Retrying in {sleep_time:.3f}s...")
                
                time.sleep(sleep_time)
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        
        raise requests.exceptions.RequestException("All retry attempts failed")
    
    def close(self):
        """Close the session and cleanup connections"""
        self.session.close()

# Global client instance
http_client = RobustHTTPClient()
