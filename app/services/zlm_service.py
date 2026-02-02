import requests
from typing import Dict, Any
from app.core.config import settings

class ZLMService:
    def __init__(self):
        self.base_url = settings.ZLM_HOST
        self.secret = settings.ZLM_SECRET

    def _get_params(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        if params is None:
            params = {}
        params["secret"] = self.secret
        return params

    def get_media_list(self) -> Dict[str, Any]:
        """
        Get list of active streams from ZLM
        """
        try:
            url = f"{self.base_url}/index/api/getMediaList"
            resp = requests.get(url, params=self._get_params())
            return resp.json()
        except Exception as e:
            print(f"Error calling ZLM getMediaList: {e}")
            return {}

    def close_stream(self, stream_id: str, app: str = "live", vhost: str = "__defaultVhost__") -> bool:
        """
        Close a stream
        """
        try:
            url = f"{self.base_url}/index/api/close_stream"
            params = self._get_params({
                "stream": stream_id,
                "app": app,
                "vhost": vhost,
                "force": "1"
            })
            resp = requests.get(url, params=params)
            data = resp.json()
            return data.get("code") == 0
        except Exception as e:
            print(f"Error calling ZLM close_stream: {e}")
            return False

zlm_service = ZLMService()
