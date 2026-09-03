import os
import subprocess
import threading
import time

from flask import Flask, Response

app = Flask(__name__)

HOST = "127.0.0.1"
PORT = 8080
SCREEN = "/tmp/maccontrol-screen.png"


def take_screenshot():
    result = subprocess.run(
        [
            "/usr/sbin/screencapture",
            "-x",
            SCREEN,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )

    return result.returncode == 0 and os.path.exists(SCREEN)


def screenshot_loop():
    while True:
        try:
            take_screenshot()
        except Exception as exc:
            print(f"Screenshot error: {exc}", flush=True)

        time.sleep(1)


@app.route("/")
def index():
    return """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <title>macOS Runner</title>

    <style>
        * {
            box-sizing: border-box;
        }

        html,
        body {
            margin: 0;
            padding: 0;
            background: #111;
            color: #fff;
            font-family: -apple-system, BlinkMacSystemFont,
                         "Segoe UI", sans-serif;
        }

        header {
            padding: 14px 18px;
            background: #1d1d1f;
            border-bottom: 1px solid #333;
        }

        h1 {
            margin: 0;
            font-size: 20px;
        }

        #status {
            margin-top: 5px;
            color: #55d68a;
            font-size: 14px;
        }

        main {
            padding: 16px;
        }

        #screen {
            display: block;
            max-width: 100%;
            height: auto;
            margin: 0 auto;
            border: 1px solid #444;
            background: #000;
        }

        #error {
            color: #ff6b6b;
            margin-top: 12px;
        }
    </style>
</head>

<body>

<header>
    <h1>macOS Runner</h1>
    <div id="status">Connecting...</div>
</header>

<main>
    <img
        id="screen"
        alt="macOS screenshot"
    >

    <div id="error"></div>
</main>

<script>
const screen = document.getElementById("screen");
const status = document.getElementById("status");
const error = document.getElementById("error");

let previousUrl = null;

async function refreshScreen() {
    try {
        const response = await fetch(
            "/screen?t=" + Date.now(),
            {
                cache: "no-store"
            }
        );

        if (!response.ok) {
            status.textContent = "Screenshot unavailable";
            error.textContent =
                "HTTP " + response.status;
            return;
        }

        const blob = await response.blob();

        const url = URL.createObjectURL(blob);

        screen.src = url;

        if (previousUrl !== null) {
            URL.revokeObjectURL(previousUrl);
        }

        previousUrl = url;

        status.textContent = "Connected";
        error.textContent = "";

    } catch (err) {
        status.textContent = "Disconnected";
        error.textContent = err.toString();
    }
}

refreshScreen();

setInterval(
    refreshScreen,
    1000
);
</script>

</body>
</html>
"""


@app.route("/screen")
def screen():
    if not os.path.exists(SCREEN):
        return (
            "Screenshot not available yet",
            503,
        )

    try:
        with open(SCREEN, "rb") as image:
            data = image.read()

        return Response(
            data,
            mimetype="image/png",
            headers={
                "Cache-Control": "no-store, no-cache, "
                                 "must-revalidate, max-age=0",
                "Pragma": "no-cache",
            },
        )

    except OSError as exc:
        return (
            f"Unable to read screenshot: {exc}",
            500,
        )


def main():
    print(
        f"Starting server on "
        f"http://{HOST}:{PORT}",
        flush=True,
    )

    screenshot_thread = threading.Thread(
        target=screenshot_loop,
        daemon=True,
    )

    screenshot_thread.start()

    app.run(
        host=HOST,
        port=PORT,
        threaded=True,
        debug=False,
    )


if __name__ == "__main__":
    main()
