import socket

class TCPClient:
    """
    TCP通信を行うクライアントを表すクラス
    """
    def request(self):
        """
        サーバーへのリクエストを送信する
        """

        print("=== クライアントを起動する ===")

        try:
            #socketを作成
            client_socket = socket.socket()
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            #サーバーと接続する
            print("=== サーバーと接続します ===")
            client_socket.connect(("127.0.0.1", 80))
            print("=== サーバーとの接続が完了しました ===")

            #サーバーに送信するリクエストを、ファイルから取得する
            with open("client_send.txt", "rb") as f:
                request = f.read()

            #サーバーへリクエストを送信する
            client_socket.send(request) #bytes型で送信する

            #サーバーからレスポンスが送られてくるのを待ち、取得する
            response = client_socket.recv(4096)

            #レスポンスの内容を、ファイルに書き出す
            with open("client_recv.txt", "wb") as f:
                f.write(response)

            #通信を終了させる
            client_socket.close()

        finally:
            print("=== クライアントを停止します ===")

if __name__ == '__main__':
    client = TCPClient()
    client.request()