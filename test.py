

import time

from poly_market_maker.lifecycle import Lifecycle



def startup():
    print("Running startup")
    time.sleep(0.1)
    print("startup done!")

def callback():
    print("Running timer callback!")
    time.sleep(1)
    print("timer callback done!")

def shutdown():
    print("Running shutdown callback!")
    time.sleep(0.1)
    print("timer shutdown done!")

def main():
    lifecycle = Lifecycle()
    with lifecycle:
        lifecycle.on_startup(startup)
        lifecycle.every(3, callback)
        lifecycle.on_shutdown(shutdown)

    print("All done!")


    pass

main()