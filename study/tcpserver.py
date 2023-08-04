"""
・TCPサーバーを作る
→ブラウザからのリクエストを受け取ってファイル(server_recv.txt)に書き出すプログラム
"""

import socket

class TCPServer:
    """
    TCP通信を行うサーバーを表すクラス
    """
    def serve(self):
        """
        サーバーを起動する
        """

        print("=== サーバーを起動します ===")

        try:
            #socketを作成（デフォルトでは、TCP通信を行うためのsocketインスタンスを生成する）
            server_socket = socket.socket()
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            #socketをlocalhostのポート8080番に割り当てる
            server_socket.bind(("localhost", 8080)) #実行中のpythonプログラムとマシンのportを紐づける
            server_socket.listen(10) #socketがbind済みのポートを実際にプログラムに割り当てる

            #外部からの接続を待ち。接続があったらコネクションを確立する
            print("=== クライアントからの接続を待ちます ===")
            (client_socket, address) = server_socket.accept() #これが成功すると、TCPのコネクションが確立したことになる
            print(f"=== クライアントとの接続が完了しました remote_address: {address} ===")

            #クライアントから送られてきたデータを取得する
            request = client_socket.recv(4096) #bytes型で取得。4096バイトずつデータを取得する。

            #クライアントから送られてきたデータをファイルに書き出す
            with open("server_recv.txt", "wb") as f:
                f.write(request)

            #クライアントへ送信するレスポンスデータをファイルから取得する
            with open("server_send.txt", "rb") as f:
                response = f.read()

            #クライアントへレスポンスを送信する
            client_socket.send(response)

            #返事は特に返さず、通信を終了させる
            client_socket.close()

        finally:
            print("=== サーバーを停止します。 ===")

if __name__ == "__main__":
    server = TCPServer()
    server.serve()