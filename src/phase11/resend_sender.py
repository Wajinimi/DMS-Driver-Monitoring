# Phase 11 — I send weekly reports through Resend (no Microsoft SMTP needed)
import json
import os
import urllib.error
import urllib.request


class ResendSender:
    def __init__(self, from_address, from_name=None, api_key_env="DMS_RESEND_API_KEY"):
        # I send from agent@neuralforgesystems.org after domain verification in Resend
        self._from_address = from_address
        self._from_name = from_name
        self._api_key_env = api_key_env

    def _get_api_key(self):
        # I read the API key from the environment — never from config.yaml or git
        api_key = os.environ.get(self._api_key_env)
        if not api_key:
            raise ValueError(
                f"I need {self._api_key_env} set in the environment "
                "(copy your key from the Resend dashboard)"
            )
        return api_key

    def _format_from(self):
        if self._from_name:
            return f"{self._from_name} <{self._from_address}>"
        return self._from_address

    def send(self, to_address, subject, plain_text_body):
        """I POST one plain-text email to the Resend API."""
        payload = {
            "from": self._format_from(),
            "to": [to_address],
            "subject": subject,
            "text": plain_text_body,
        }

        request = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + self._get_api_key(),
                "Content-Type": "application/json",
                # Resend blocks requests without User-Agent (error 1010)
                "User-Agent": "DMS-Weekly-Report/1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Resend API error {err.code}: {body}"
            ) from err

        return result
