import time
import gc
import threading


class RuntimeCleanup:

    def __init__(self, interval=30):
        self.interval = interval
        self.running = True

    def start(self):
        t = threading.Thread(target=self.run, daemon=True)
        t.start()

    def run(self):
        while self.running:
            try:
                # 🔥 Force Python garbage collect
                gc.collect()

                # giảm fragmentation (optional)
                try:
                    gc.collect(2)
                except:
                    pass

            except Exception as e:
                print("[RUNTIME CLEAN ERROR]", e)

            time.sleep(self.interval)