#!/usr/bin/env python3
"""
Production-ready script to fetch full runtime and build/deploy logs from Render.com API.

Requirements:
    pip install requests

Usage:
    export RENDER_API_KEY="rnd_..."
    python fetch_render_logs.py --hours 24
    python fetch_render_logs.py --hours 6 --service jobhuntin-job-queue
    python fetch_render_logs.py --hours 48 --output-dir ./custom_logs
"""

import argparse
import datetime
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


class RenderLogsFetcher:
    """Fetch logs from Render.com API with proper pagination and error handling."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.render.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _make_request_with_retry(self, url: str, params: Optional[Dict] = None, max_retries: int = 3) -> requests.Response:
        """Make API request with exponential backoff for rate limits."""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params)

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 2))
                    wait_time = retry_after * (2 ** attempt)  # Exponential backoff
                    print(f"Rate limited, waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

                return response

            except requests.exceptions.RequestException:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                print(f"Request failed, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)

        return response

    def discover_services(self) -> List[Dict[str, Any]]:
        """Discover all services with pagination support."""
        print("🔍 Discovering services...")
        services = []
        cursor = None

        while True:
            params = {}
            if cursor:
                params['cursor'] = cursor

            try:
                response = self._make_request_with_retry(f"{self.base_url}/services", params)

                if response.status_code == 401:
                    raise Exception("Invalid API key. Please check your RENDER_API_KEY.")
                elif response.status_code != 200:
                    raise Exception(f"Failed to fetch services: {response.status_code} - {response.text}")

                data = response.json()
                print(f"📊 Raw response type: {type(data)}")

                # Handle different response formats
                if isinstance(data, list):
                    # Each item is a dict with 'service' key
                    for item in data:
                        if isinstance(item, dict) and 'service' in item:
                            services.append(item['service'])
                    break  # No pagination for list response
                elif isinstance(data, dict):
                    # Try different possible keys
                    if 'services' in data:
                        services.extend(data['services'])
                    elif 'data' in data:
                        services.extend(data['data'])
                    else:
                        # If it's a dict but doesn't have expected keys, print structure
                        print(f"📊 Response keys: {list(data.keys())}")
                        # Try to extract services from nested structure
                        for key, value in data.items():
                            if isinstance(value, list):
                                print(f"📊 Found list in key '{key}' with {len(value)} items")
                                if value and isinstance(value[0], dict):
                                    print(f"📊 First item keys: {list(value[0].keys())}")
                                    services.extend(value)
                                    break

                    # Check for pagination
                    cursor = data.get('cursor')
                    if not cursor:
                        break
                else:
                    print(f"📊 Unexpected response format: {type(data)}")
                    break

            except Exception as e:
                print(f"❌ Error discovering services: {e}")
                raise

        print(f"✅ Found {len(services)} services")
        return services

    def get_service_deploys(self, service_id: str) -> List[Dict[str, Any]]:
        """Get recent deploys for a service to capture build logs."""
        try:
            response = self._make_request_with_retry(f"{self.base_url}/services/{service_id}/deploys")

            if response.status_code == 200:
                deploys = response.json()
                if isinstance(deploys, list):
                    return deploys[:5]  # Get last 5 deploys
                elif isinstance(deploys, dict) and 'data' in deploys:
                    return deploys['data'][:5]
                return []
            else:
                print(f"⚠️  Could not fetch deploys for {service_id}: {response.status_code}")
                return []

        except Exception as e:
            print(f"⚠️  Error fetching deploys for {service_id}: {e}")
            return []

    def fetch_logs_for_service(self, service: Dict[str, Any], hours: int) -> List[Dict[str, Any]]:
        """Fetch all logs for a specific service."""
        service_name = service.get('name', service.get('slug', 'unknown'))
        service_id = service.get('id')
        service_type = service.get('type', 'unknown')
        status = service.get('status', 'unknown')
        owner_id = service.get('ownerId')

        print(f"📋 Fetching logs for {service_name} ({service_type}, status: {status})")
        print(f"  📋 Service ID: {service_id}")
        print(f"  📋 Owner ID: {owner_id}")

        # Calculate time range
        end_time = datetime.datetime.now(datetime.timezone.utc)
        start_time = end_time - datetime.timedelta(hours=hours)

        # Convert to RFC3339 format (as per API docs)
        start_timestamp = start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end_timestamp = end_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        all_logs = []

        # First, try to get runtime logs
        try:
            runtime_logs = self._fetch_logs_with_pagination(
                resource_ids=[service_id],
                owner_id=owner_id,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                log_type="runtime"
            )
            all_logs.extend(runtime_logs)
            print(f"  📊 Runtime logs: {len(runtime_logs)} entries")
        except Exception as e:
            print(f"  ⚠️  Could not fetch runtime logs: {e}")

        # Then, get build/deploy logs
        try:
            deploys = self.get_service_deploys(service_id)
            deploy_logs = []

            for deploy in deploys:
                deploy_id = deploy.get('id')
                deploy_status = deploy.get('status', 'unknown')

                # Get logs for this specific deploy
                try:
                    deploy_log_entries = self._fetch_logs_with_pagination(
                        resource_ids=[service_id],
                        owner_id=owner_id,
                        start_timestamp=start_timestamp,
                        end_timestamp=end_timestamp,
                        deploy_id=deploy_id,
                        log_type=f"deploy-{deploy_status}"
                    )
                    deploy_logs.extend(deploy_log_entries)

                except Exception as e:
                    print(f"    ⚠️  Could not fetch logs for deploy {deploy_id}: {e}")

            all_logs.extend(deploy_logs)
            print(f"  🔨 Deploy logs: {len(deploy_logs)} entries")

        except Exception as e:
            print(f"  ⚠️  Could not fetch deploy logs: {e}")

        print(f"  ✅ Total logs for {service_name}: {len(all_logs)} entries")
        return all_logs

    def _fetch_logs_with_pagination(self, resource_ids: List[str], owner_id: str, start_timestamp: int,
                                   end_timestamp: int, deploy_id: Optional[str] = None,
                                   log_type: str = "general") -> List[Dict[str, Any]]:
        """Fetch logs with proper pagination handling."""
        all_logs = []
        page_count = 0

        while True:
            page_count += 1
            print(f"    📄 Fetching page {page_count}...")

            # Build query parameters according to API spec
            params = {
                'ownerId': owner_id,
                'resource[]': resource_ids,  # Array parameter
                'startTime': start_timestamp,
                'endTime': end_timestamp
            }

            if deploy_id:
                params['deployId'] = deploy_id

            try:
                response = self._make_request_with_retry(f"{self.base_url}/logs", params)

                if response.status_code == 404:
                    print("    ⚠️  Logs endpoint not found (404) - this is expected for some service types")
                    break
                elif response.status_code != 200:
                    print(f"    ⚠️  Failed to fetch logs: {response.status_code} - {response.text}")
                    break

                data = response.json()

                # Handle different response formats
                logs = []
                has_more = False
                next_start_time = None
                next_end_time = None

                if isinstance(data, list):
                    logs = data
                elif isinstance(data, dict):
                    logs = data.get('logs', [])
                    has_more = data.get('hasMore', False)
                    next_start_time = data.get('nextStartTime')
                    next_end_time = data.get('nextEndTime')

                if not logs:
                    print("    📝 No more logs found")
                    break

                # Add metadata to each log entry
                for log in logs:
                    if isinstance(log, dict):
                        log['_fetch_metadata'] = {
                            'log_type': log_type,
                            'page': page_count,
                            'deploy_id': deploy_id
                        }

                all_logs.extend(logs)
                print(f"    📊 Page {page_count}: {len(logs)} entries")

                # Check pagination
                if not has_more:
                    print("    ✅ All logs fetched")
                    break

                # Update timestamps for next page
                if next_start_time and next_end_time:
                    start_timestamp = next_start_time
                    end_timestamp = next_end_time
                else:
                    # Fallback: use timestamp of last log
                    if logs and isinstance(logs[-1], dict):
                        last_timestamp = logs[-1].get('timestamp')
                        if last_timestamp:
                            start_timestamp = last_timestamp

            except Exception as e:
                print(f"    ❌ Error fetching page {page_count}: {e}")
                break

        return all_logs

    def sanitize_filename(self, name: str) -> str:
        """Sanitize service name for filename."""
        # Replace invalid characters with underscores
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        # Ensure it's not empty
        return sanitized or 'unknown_service'

    def write_logs_to_file(self, service: Dict[str, Any], logs: List[Dict[str, Any]], output_dir: str):
        """Write logs to a file for the service."""
        service_name = service.get('name', service.get('slug', 'unknown'))
        filename = self.sanitize_filename(service_name) + '.log'
        filepath = Path(output_dir) / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write header
                f.write(f"# Render Logs for {service_name}\n")
                f.write(f"# Service ID: {service.get('id')}\n")
                f.write(f"# Type: {service.get('type')}\n")
                f.write(f"# Status: {service.get('status')}\n")
                f.write(f"# Region: {service.get('region')}\n")
                f.write(f"# Generated: {datetime.datetime.now().isoformat()}\n")
                f.write(f"# Total Log Entries: {len(logs)}\n")
                f.write("#" + "=" * 80 + "\n\n")

                # Write logs
                for log in logs:
                    if isinstance(log, dict):
                        timestamp = log.get('timestamp', 'N/A')
                        level = log.get('level', 'N/A')
                        message = log.get('message', '')
                        metadata = log.get('_fetch_metadata', {})

                        f.write(f"[{timestamp}] [{level}]")
                        if metadata.get('log_type'):
                            f.write(f" [{metadata['log_type']}]")
                        f.write(f" {message}\n")
                    else:
                        f.write(f"{log}\n")

            print(f"  💾 Logs written to {filepath}")

        except Exception as e:
            print(f"  ❌ Error writing logs to file: {e}")


def main():
    parser = argparse.ArgumentParser(description='Fetch logs from Render.com services')
    parser.add_argument('--hours', type=int, default=24, help='Hours of logs to fetch (default: 24)')
    parser.add_argument('--service', type=str, help='Fetch logs for specific service only')
    parser.add_argument('--output-dir', type=str, default='./logs', help='Output directory (default: ./logs)')

    args = parser.parse_args()

    # Check API key
    api_key = os.getenv('RENDER_API_KEY')
    if not api_key:
        print("❌ Error: RENDER_API_KEY environment variable not set")
        print("Please set your API key: export RENDER_API_KEY='rnd_...'")
        return 1

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Initialize fetcher
    fetcher = RenderLogsFetcher(api_key)

    try:
        # Discover services
        services = fetcher.discover_services()

        # Filter by service name if specified
        if args.service:
            services = [s for s in services if s.get('name') == args.service or s.get('slug') == args.service]
            if not services:
                print(f"❌ Service '{args.service}' not found")
                return 1
            print(f"🎯 Targeting specific service: {args.service}")

        # Fetch logs for each service
        total_logs = 0
        for service in services:
            try:
                logs = fetcher.fetch_logs_for_service(service, args.hours)
                fetcher.write_logs_to_file(service, logs, str(output_dir))
                total_logs += len(logs)
            except Exception as e:
                print(f"❌ Error processing service {service.get('name', 'unknown')}: {e}")
                continue

        print(f"\n✅ Completed! Total log entries fetched: {total_logs}")
        print(f"📁 Logs saved to: {output_dir.absolute()}")

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
