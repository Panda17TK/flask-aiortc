import logging
import secrets
import uuid
import aiortc as aio
import asyncio
from flask import Flask, render_template, request, make_response, jsonify
from flask_cors import CORS

import exception_handler
from my_media_transform_check import AudioTransformTrack, VideoTransformTrack
from settings import Settings

# settings = Settings()
app = Flask(__name__, static_folder="./build/static", template_folder="./build/templates/")
CORS(app)  # Cross Origin Resource Sharing

app.config["TEMPLATES_AUTO_RELOAD"] = True

# 例外ハンドラの登録
exception_handler.init_app(app)

# このアプリケーションのログ設定
root_logger = logging.getLogger("app")
root_logger.addHandler(logging.StreamHandler())
# root_logger.setLevel(settings.LOG_LEVEL)

pcs = set()
dcs = set()

# 独自のイベントループを作成
event_loop = asyncio.new_event_loop()
asyncio.set_event_loop(event_loop)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    """ヘルスチェック"""
    return jsonify({"message": "It worked!!"})


@app.route("/offer", methods=["POST"])
def offer():
    params = request.json
    offer = aio.RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = aio.RTCPeerConnection()
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pcs.add(pc)

    def log_info(msg, *args):
        root_logger.info(pc_id + " " + msg, *args)

    @pc.on("datachannel")
    def on_datachannel(channel):
        dcs.add(channel)

        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        log_info("Connection state is %s", pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        log_info("Track {} received".format(track.kind))

        if track.kind == "audio":
            pc.addTrack(AudioTransformTrack(relay.subscribe(track)))
            # recorder.addTrack(track)
            # recorder.addTrack(player.audio)
            pass
        elif track.kind == "video":
            # pc.addTrack(relay.subscribe(track))
            pc.addTrack(VideoTransformTrack(relay.subscribe(track), transform=""))
            # recorder.addTrack(relay.subscribe(track))
            pass

        @track.on("ended")
        async def on_ended():
            log_info("Track %s ended", track.kind)
            await aio.recorder.stop()

    # handle offer
    event_loop.run_until_complete(pc.setRemoteDescription(offer))
    event_loop.run_until_complete(aio.recorder.start())

    # send answer
    answer = event_loop.run_until_complete(pc.createAnswer())
    event_loop.run_until_complete(pc.setLocalDescription(answer))

    return jsonify(
        {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
    )


@app.route("/message", methods=["POST"])
def message():
    params = request.json
    [dc.send(params["message"]) for dc in dcs]

    return jsonify({"message": "Message sent"})


@app.teardown_appcontext
def on_shutdown(exception=None):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    event_loop.run_until_complete(asyncio.gather(*coros))
    pcs.clear()


if __name__ == "__main__":
    app.debug = True
    app.run(host='127.0.0.1', port=5000, threaded=True)
