import os
import re
import traceback
from datetime import datetime
from socket import socket
from threading import Thread
from typing import Optional, Tuple

import views
from henango.http.request import HTTPRequest
from henango.http.response import HTTPResponse
from urls import URL_VIEW


class WorkerThread(Thread):
    #実行ファイルのあるディレクトリ
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    #性的配信するファイルを置くディレクトリ
    STATIC_ROOT = os.path.join(BASE_DIR, "static")

    #拡張子とMIME Typeの対応
    MIME_TYPES = {
        "html": "text/html; charset=UTF-8",
        "css": "text/css",
        "png": "image/png",
        "jpg": "image/jpg",
        "gif": "image/gif"
    }

    #ステータスコードとステータスラインの対応
    STATUS_LINES = {
        200: "200 OK",
        404: "404 Not Found",
        405: "405 Method Not Allowed"
    }

    def __init__(self, client_socket: socket, address: Tuple[str, int]):
        super().__init__()

        self.client_socket = client_socket
        self.client_address = address

    def run(self) -> None:
        """
        クライアントと接続済みのsocketを引数として受け取り、
        リクエストを処理してレスポンスを送信する
        """

        try:
            # クライアントから送られてきたデータを取得する
            request = self.client_socket.recv(4096)

            # クライアントから送られてきたデータをファイルに書き出す
            with open("server_recv.txt", "wb") as f:
                f.write(request)

            # HTTPリクエストをパースする
            method, path, http_version, request_header, request_body = self.parse_http_request(request)

            #pathに対応するview関数があれば、関数を取得して呼び出し、レスポンスを生成する
            if request.path in URL_VIEW:
                view = URL_VIEW[request.path]
                response = view(request)

            #pathがそれ以外のときは、静的ファイルからレスポンセ羽を生成する
            else:
                try:
                    # ファイルからレスポンスボディを生成
                    response_body = self.get_static_file_content(request.path)

                    #Content_Typeを指定
                    content_type = None

                    # レスポンスラインを生成
                    response = HTTPResponse(body=response_body, content_type=content_type, status_code = 404)

                except OSError:
                    #レスポンスを取得できなかった場合は、ログを出力して404を返す
                    traceback.print_exc()

                    response_body = b"<html><body><h1>404 Not Found</h1></body></html>"
                    content_type = "text/html; charset=UTF-8"
                    response_line = "HTTP/1.1 404 Not Found\r\n"

            #レスポンスラインを生成
            response_line = self.build_response_line(response)

            # レスポンスヘッダーを生成
            response_header = self.build_response_header(path, response_body, content_type)

            # レスポンス全体を生成する
            response = (response_line + response_header + "\r\n").encode() + response_body

            # クライアントへレスポンスを送信する
            self.client_socket.send(response)

        except Exception:
            # リクエストの処理中に例外が発生した場合はコンソールにエラーログを出力し、
            # 処理を続行する
            print("=== Worker: リクエストの処理中にエラーが発生しました ===")
            traceback.print_exc()

        finally:
            # 例外が発生した場合も、発生しなかった場合も、TCP通信のcloseは行う
            print(f"=== Worker: クライアントとの通信を終了します remote_address: {self.client_address} ===")
            self.client_socket.close()

    def parse_http_request(self, request: bytes) -> Tuple[str, str, str, dict, bytes]:
        """_summary_
        HTTPリクエストを
        1. method: str
        2. path: str
        3. http_version: str
        4. request_header: bytes
        5. request_body: bytes
        に分割・変換する
        Args:
            requests (bytes): _description_

        Returns:
            Tuple[str, str, str, bytes, bytes]: _description_
        """

        # リクエスト全体を
        # 1. リクエストライン(1行目)
        # 2. リクエストヘッダー(2行目〜空行)
        # 3. リクエストボディ(空行〜)
        # にパースする
        request_line, remain = request.split(b"\r\n", maxsplit=1)
        request_header, request_body = remain.split(b"\r\n\r\n", maxsplit=1)

        #リクエストラインを文字列に変換してパースする
        method, path, http_version = request_line.decode().split(" ")

        #リクエストヘッダーを辞書にパースする
        headers = {}
        for header_row in request_header.decode().split("\r\n"):
            key, value = re.split(r": *", header_row, maxsplit=1)
            headers[key] = value

        return method, path, http_version, request_header, request_body

    def get_static_file_content(self, path: str) -> bytes:
        """_summary_
        リクエストpathから、staticファイルの内容を取得する
        Args:
            path (str): _description_

        Returns:
            bytes: _description_
        """
        #pathの先頭の/を削除し、相対パスにしておく
        relative_path = path.lstrip("/")
        #ファイルのpathを取得
        static_file_path = os.path.join(self.STATIC_ROOT, relative_path)

        with open(static_file_path, "rb") as f:
            return f.read()

    def build_response_line(self, response: HTTPResponse) -> str:
        """
        レスポンスラインを構築する
        Args:
            response (HTTPResponse): _description_

        Returns:
            str: _description_
        """
        status_line = self.STATUS_LINES[response.status_code]

        return f"HTTP/1.1 {status_line}"

    def build_response_header(self, path: str, response_body: bytes, content_type: Optional[str]) -> str:
        """_summary_
        レスポンスヘッダーを構築する
        Args:
            path (str): _description_
            response_body (bytes): _description_
        Returns:
            str: _description_
        """
        #Contetn-Typeが指定されてない場合は、pathから指定する
        if content_type is None:
            #pathから拡張子を取得
            if "." in path:
                ext = path.rsplit(".", maxsplit=1)[-1]
            else:
                ext = ""
            #拡張子からMIME Typeを取得
            #知らない対応していない拡張子の場合はoctet-streamとする
            content_type = self.MIME_TYPES.get(ext, "application/octet-stream")

        # レスポンスヘッダーを生成
        response_header = ""
        response_header += f"Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
        response_header += "Host: HenaServer/0.1\r\n"
        response_header += f"Content-Length: {len(response_body)}\r\n"
        response_header += "Connection: Close\r\n"
        response_header += f"Content-Type: {content_type}\r\n"

        return response_header
