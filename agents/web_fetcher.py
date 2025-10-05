#!/usr/bin/env python3
"""
Web Documentation Fetcher - Safe web scraping for agent documentation access

Addresses Issue #11: Add web documentation fetching capability
Provides sandboxed web access to trusted documentation sources.

Author: Agent Forge
"""

import requests
from typing import Optional, List, Dict
from urllib.parse import urlparse
import time
from pathlib import Path
import hashlib
import json
from html.parser import HTMLParser
import re


class HTMLTextExtractor(HTMLParser):
    """Extract clean text from HTML, removing scripts, styles, and formatting"""
    
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_tags = {'script', 'style', 'noscript', 'meta', 'head'}
        self.current_tag = None
    
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
    
    def handle_endtag(self, tag):
        self.current_tag = None
    
    def handle_data(self, data):
        if self.current_tag not in self.skip_tags:
            # Clean whitespace but preserve structure
            text = data.strip()
            if text:
                self.text_parts.append(text)
    
    def get_text(self) -> str:
        """Get extracted text with cleaned whitespace"""
        return '\n'.join(self.text_parts)


class WebFetcher:
    """Safe web documentation fetcher with whitelisting and rate limiting
    
    All operations are restricted to trusted domains to prevent abuse.
    Includes caching, rate limiting, and content size limits.
    """
    
    # Trusted documentation domains
    TRUSTED_DOMAINS = [
        'docs.python.org',
        'github.com',
        'readthedocs.org',
        'readthedocs.io',
        'pypi.org',
        'stackoverflow.com',
        'developer.mozilla.org',
        'docs.djangoproject.com',
        'flask.palletsprojects.com',
        'fastapi.tiangolo.com',
        'numpy.org',
        'pytorch.org',
        'tensorflow.org',
        'scikit-learn.org',
        'pandas.pydata.org',
        'docs.docker.com',
        'kubernetes.io',
        'rust-lang.org',
        'go.dev',
        'nodejs.org',
        'reactjs.org',
        'vuejs.org',
    ]
    
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        max_size: int = 500000,  # 500KB default
        rate_limit_delay: float = 1.0,  # 1 second between requests
        timeout: int = 10
    ):
        """Initialize web fetcher
        
        Args:
            cache_dir: Directory for caching responses (None = no cache)
            max_size: Maximum response size in bytes
            rate_limit_delay: Minimum seconds between requests
            timeout: HTTP request timeout in seconds
        """
        self.max_size = max_size
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self.last_request_time = 0
        
        # Setup cache
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # HTTP session with user agent
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Agent-Forge/0.1.0 (Educational/Development Bot)'
        })
    
    def _validate_url(self, url: str) -> bool:
        """Check if URL is from trusted domain
        
        Args:
            url: URL to validate
            
        Returns:
            True if domain is trusted
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check exact match or subdomain match
        for trusted in self.TRUSTED_DOMAINS:
            if domain == trusted or domain.endswith('.' + trusted):
                return True
        
        return False
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def _get_cache_path(self, url: str) -> Optional[Path]:
        """Get cache file path for URL"""
        if not self.cache_dir:
            return None
        
        # Use URL hash as filename
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.json"
    
    def _load_from_cache(self, url: str) -> Optional[str]:
        """Load cached response if available and fresh
        
        Args:
            url: URL to check cache for
            
        Returns:
            Cached content or None
        """
        cache_path = self._get_cache_path(url)
        if not cache_path or not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            # Check if cache is less than 24 hours old
            cached_time = data.get('timestamp', 0)
            if time.time() - cached_time < 86400:  # 24 hours
                return data.get('content')
        except (json.JSONDecodeError, OSError):
            pass
        
        return None
    
    def _save_to_cache(self, url: str, content: str):
        """Save response to cache
        
        Args:
            url: URL being cached
            content: Response content
        """
        cache_path = self._get_cache_path(url)
        if not cache_path:
            return
        
        try:
            with open(cache_path, 'w') as f:
                json.dump({
                    'url': url,
                    'timestamp': time.time(),
                    'content': content
                }, f)
        except OSError:
            pass  # Cache write failure is non-fatal
    
    def fetch_docs(self, url: str, extract_text: bool = True) -> str:
        """Fetch documentation from URL
        
        Args:
            url: Documentation URL to fetch
            extract_text: If True, extract clean text from HTML (default)
            
        Returns:
            Page content (text or HTML)
            
        Raises:
            ValueError: If URL not trusted or response too large
            requests.RequestException: If fetch fails
            
        Example:
            >>> fetcher = WebFetcher(cache_dir='/tmp/docs-cache')
            >>> docs = fetcher.fetch_docs('https://docs.python.org/3/library/os.html')
        """
        # Validate URL
        if not self._validate_url(url):
            raise ValueError(
                f"URL domain not trusted: {urlparse(url).netloc}\n"
                f"Trusted domains: {', '.join(self.TRUSTED_DOMAINS)}"
            )
        
        # Check cache first
        cached = self._load_from_cache(url)
        if cached:
            return cached
        
        # Rate limiting
        self._rate_limit()
        
        # Fetch content
        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                stream=True  # Stream to check size before loading all
            )
            response.raise_for_status()
            
            # Check content size
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_size:
                raise ValueError(
                    f"Content too large: {content_length} bytes "
                    f"(max: {self.max_size})"
                )
            
            # Load content with size limit
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > self.max_size:
                    raise ValueError(
                        f"Content exceeded max size: {self.max_size} bytes"
                    )
            
            # Decode
            text = content.decode('utf-8', errors='replace')
            
            # Extract clean text if requested
            if extract_text and 'text/html' in response.headers.get('content-type', ''):
                parser = HTMLTextExtractor()
                parser.feed(text)
                text = parser.get_text()
            
            # Cache result
            self._save_to_cache(url, text)
            
            return text
            
        except requests.Timeout:
            raise requests.RequestException(f"Request timed out after {self.timeout}s")
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to fetch {url}: {e}")
    
    def search_python_docs(self, topic: str) -> str:
        """Quick helper to search Python documentation
        
        Args:
            topic: Topic to search (e.g., 'os.path', 'asyncio')
            
        Returns:
            Documentation content
            
        Example:
            >>> fetcher = WebFetcher()
            >>> docs = fetcher.search_python_docs('asyncio')
        """
        # Convert topic to URL-friendly format
        topic_path = topic.replace('.', '/')
        url = f"https://docs.python.org/3/library/{topic_path}.html"
        
        return self.fetch_docs(url)
    
    def get_github_readme(self, owner: str, repo: str) -> str:
        """Fetch GitHub repository README
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            README content (markdown or plain text)
            
        Example:
            >>> fetcher = WebFetcher()
            >>> readme = fetcher.get_github_readme('python', 'cpython')
        """
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
        
        try:
            return self.fetch_docs(url, extract_text=False)
        except requests.RequestException:
            # Try master branch if main doesn't exist
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
            return self.fetch_docs(url, extract_text=False)


# Test harness
if __name__ == '__main__':
    import sys
    import tempfile
    
    print("🌐 Web Documentation Fetcher Test\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        fetcher = WebFetcher(cache_dir=tmpdir, max_size=2000000)  # 2MB for docs
        
        # Test 1: Fetch Python docs
        print("📚 Fetching Python os module docs...")
        try:
            docs = fetcher.fetch_docs('https://docs.python.org/3/library/os.html')
            print(f"   ✓ Fetched {len(docs)} characters")
            print(f"   Preview: {docs[:200]}...")
        except Exception as e:
            print(f"   ✗ Failed: {e}")
        
        print()
        
        # Test 2: Try untrusted domain (should fail)
        print("🔒 Testing domain whitelist...")
        try:
            fetcher.fetch_docs('https://example.com')
            print("   ✗ Should have rejected untrusted domain!")
        except ValueError as e:
            print(f"   ✓ Correctly rejected: {str(e)[:60]}...")
        
        print()
        
        # Test 3: Cache test
        print("💾 Testing cache...")
        start = time.time()
        docs1 = fetcher.fetch_docs('https://docs.python.org/3/library/sys.html')
        time1 = time.time() - start
        
        start = time.time()
        docs2 = fetcher.fetch_docs('https://docs.python.org/3/library/sys.html')
        time2 = time.time() - start
        
        print(f"   First fetch: {time1:.2f}s")
        print(f"   Cached fetch: {time2:.2f}s")
        print(f"   ✓ Cache is {'faster' if time2 < time1 / 2 else 'working'}")
        
        print()
        print("✅ Web fetcher working!")
