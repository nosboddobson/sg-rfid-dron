import os
import socket
import threading

import servicemanager
import win32event
import win32service
import win32serviceutil

from waitress.server import create_server

from Server import app


class InventarioDronApiService(win32serviceutil.ServiceFramework):
    _svc_name_ = "Inventario_Dron_Server"
    _svc_display_name_ = "Inventario Dron Server"
    _svc_description_ = "Flask API service for Sierra Dron inventory backend (native pywin32 service)."

    def __init__(self, args):
        super().__init__(args)
        self.h_wait_stop = win32event.CreateEvent(None, 0, 0, None)
        self.http_server = None
        self.server_thread = None

    def _build_server(self):
        host = os.getenv("API_HOST", "0.0.0.0")
        port = int(os.getenv("API_PORT", "5100"))

        # API_HOST in this project is usually a fixed LAN IP; if invalid in this host,
        # fallback to all interfaces so the service can still boot.
        try:
            socket.gethostbyname(host)
        except Exception:
            host = "0.0.0.0"

        self.http_server = create_server(
            app,
            host=host,
            port=port,
            threads=8,
            _quiet=True,
        )

    def _serve(self):
        self.http_server.run()

    def SvcDoRun(self):
        servicemanager.LogInfoMsg(f"{self._svc_name_}: starting")
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)

        try:
            self._build_server()
            self.server_thread = threading.Thread(target=self._serve, daemon=True)
            self.server_thread.start()

            win32event.WaitForSingleObject(self.h_wait_stop, win32event.INFINITE)
        except Exception as exc:
            servicemanager.LogErrorMsg(f"{self._svc_name_}: fatal error: {exc}")
            raise
        finally:
            if self.http_server is not None:
                try:
                    self.http_server.close()
                except Exception:
                    pass

            if self.server_thread is not None:
                self.server_thread.join(timeout=10)

        servicemanager.LogInfoMsg(f"{self._svc_name_}: stopped")

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        if self.http_server is not None:
            try:
                self.http_server.close()
            except Exception:
                pass

        win32event.SetEvent(self.h_wait_stop)


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(InventarioDronApiService)
