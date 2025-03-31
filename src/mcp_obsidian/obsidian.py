import urllib.parse
from typing import Any

import requests


class Obsidian:
    """Obsidian Local REST API client for interacting with Obsidian vault.

    This class provides methods to interact with an Obsidian vault through the Local REST API.
    It supports operations like listing files, reading contents, searching, and modifying notes.
    """

    def __init__(
        self,
        api_key: str,
        protocol: str = "https",
        host: str = "127.0.0.1",
        port: int = 27124,
        verify_ssl: bool = False,
    ):
        """Initialize the Obsidian API client.

        Args:
            api_key: The API key for authentication
            protocol: The protocol to use (http/https)
            host: The host address of the Obsidian Local REST API
            port: The port number of the Obsidian Local REST API
            verify_ssl: Whether to verify SSL certificates
        """
        self.api_key = api_key
        self.protocol = protocol
        self.host = host
        self.port = port
        self.verify_ssl = verify_ssl
        self.timeout = (3, 6)

    def get_base_url(self) -> str:
        """Get the base URL for the Obsidian Local REST API.

        Returns:
            The base URL string
        """
        return f"{self.protocol}://{self.host}:{self.port}"

    def _get_headers(self) -> dict:
        """Get the headers required for API requests.

        Returns:
            Dictionary containing the authorization header
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return headers

    def _safe_call(self, f) -> Any:
        """Safely execute an API call and handle errors.

        Args:
            f: Function to execute that makes the API call

        Returns:
            The result of the API call

        Raises:
            Exception: If the API call fails
        """
        try:
            return f()
        except requests.HTTPError as e:
            error_data = e.response.json() if e.response.content else {}
            code = error_data.get("errorCode", -1)
            message = error_data.get("message", "<unknown>")
            raise Exception(f"Error {code}: {message}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def list_files_in_vault(self) -> Any:
        """List all files in the Obsidian vault.

        Returns:
            List of files in the vault
        """
        url = f"{self.get_base_url()}/vault/"

        def call_fn():
            response = requests.get(
                url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            return response.json()["files"]

        return self._safe_call(call_fn)

    def list_files_in_dir(self, dirpath: str) -> Any:
        """List files in a specific directory in the vault.

        Args:
            dirpath: Path to the directory relative to vault root

        Returns:
            List of files in the specified directory
        """
        url = f"{self.get_base_url()}/vault/{dirpath}/"

        def call_fn():
            response = requests.get(
                url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            return response.json()["files"]

        return self._safe_call(call_fn)

    def get_file_contents(self, filepath: str) -> Any:
        """Get the contents of a specific file.

        Args:
            filepath: Path to the file relative to vault root

        Returns:
            Contents of the specified file
        """
        url = f"{self.get_base_url()}/vault/{filepath}"

        def call_fn():
            response = requests.get(
                url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            return response.text

        return self._safe_call(call_fn)

    def get_batch_file_contents(self, filepaths: list[str]) -> str:
        """Get contents of multiple files and concatenate them with headers.

        Args:
            filepaths: List of file paths to read

        Returns:
            String containing all file contents with headers
        """
        result = []

        for filepath in filepaths:
            try:
                content = self.get_file_contents(filepath)
                result.append(f"# {filepath}\n\n{content}\n\n---\n\n")
            except Exception as e:
                # Add error message but continue processing other files
                result.append(
                    f"# {filepath}\n\nError reading file: {str(e)}\n\n---\n\n"
                )

        return "".join(result)

    def search(self, query: str, context_length: int = 100) -> Any:
        """Search for content in the vault.

        Args:
            query: Search query string
            context_length: Number of characters of context to return around matches

        Returns:
            Search results with matching content and context
        """
        url = f"{self.get_base_url()}/search/simple/"
        params = {"query": query, "contextLength": context_length}

        def call_fn():
            response = requests.post(
                url,
                headers=self._get_headers(),
                params=params,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)

    def append_content(self, filepath: str, content: str) -> Any:
        """Append content to a file.

        Args:
            filepath: Path to the file relative to vault root
            content: Content to append

        Returns:
            None on success
        """
        url = f"{self.get_base_url()}/vault/{filepath}"

        def call_fn():
            response = requests.post(
                url,
                headers=self._get_headers() | {"Content-Type": "text/markdown"},
                data=content,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return None

        return self._safe_call(call_fn)

    def patch_content(
        self, filepath: str, operation: str, target_type: str, target: str, content: str
    ) -> Any:
        """Patch content in a file relative to a specific target.

        Args:
            filepath: Path to the file relative to vault root
            operation: Operation to perform (append, prepend, replace)
            target_type: Type of target (heading, block, frontmatter)
            target: Target identifier
            content: Content to patch

        Returns:
            None on success
        """
        url = f"{self.get_base_url()}/vault/{filepath}"

        headers = self._get_headers() | {
            "Content-Type": "text/markdown",
            "Operation": operation,
            "Target-Type": target_type,
            "Target": urllib.parse.quote(target),
        }

        def call_fn():
            response = requests.patch(
                url,
                headers=headers,
                data=content,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return None

        return self._safe_call(call_fn)

    def search_json(self, query: dict) -> Any:
        """Perform a complex search using JsonLogic query.

        Args:
            query: JsonLogic query object

        Returns:
            Search results matching the query
        """
        url = f"{self.get_base_url()}/search/"

        headers = self._get_headers() | {
            "Content-Type": "application/vnd.olrapi.jsonlogic+json"
        }

        def call_fn():
            response = requests.post(
                url,
                headers=headers,
                json=query,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)

    def get_periodic_note(self, period: str) -> Any:
        """Get current periodic note for the specified period.

        Args:
            period: The period type (daily, weekly, monthly, quarterly, yearly)

        Returns:
            Content of the periodic note
        """
        url = f"{self.get_base_url()}/periodic/{period}/"

        def call_fn():
            response = requests.get(
                url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            return response.text

        return self._safe_call(call_fn)

    def get_recent_periodic_notes(
        self, period: str, limit: int = 5, include_content: bool = False
    ) -> Any:
        """Get most recent periodic notes for the specified period type.

        Args:
            period: The period type (daily, weekly, monthly, quarterly, yearly)
            limit: Maximum number of notes to return (default: 5)
            include_content: Whether to include note content (default: False)

        Returns:
            List of recent periodic notes
        """
        url = f"{self.get_base_url()}/periodic/{period}/recent"
        params = {"limit": limit, "includeContent": include_content}

        def call_fn():
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            return response.json()

        return self._safe_call(call_fn)

    def get_recent_changes(self, limit: int = 10, days: int = 90) -> Any:
        """Get recently modified files in the vault.

        Args:
            limit: Maximum number of files to return (default: 10)
            days: Only include files modified within this many days (default: 90)

        Returns:
            List of recently modified files with metadata
        """
        # Build the DQL query
        query_lines = [
            "TABLE file.mtime",
            f"WHERE file.mtime >= date(today) - dur({days} days)",
            "SORT file.mtime DESC",
            f"LIMIT {limit}",
        ]

        # Join with proper DQL line breaks
        dql_query = "\n".join(query_lines)

        # Make the request to search endpoint
        url = f"{self.get_base_url()}/search/"
        headers = self._get_headers() | {
            "Content-Type": "application/vnd.olrapi.dataview.dql+txt"
        }

        def call_fn():
            response = requests.post(
                url,
                headers=headers,
                data=dql_query.encode("utf-8"),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)
