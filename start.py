from multiprocessing import Process, Queue

import game, assistant

if __name__ == "__main__":
    assistant_send_queue = Queue()
    assistant_receive_queue = Queue()

    game_process = Process(target=game.run, args=(assistant_receive_queue, assistant_send_queue))
    assistant_process = Process(target=assistant.run, args=(assistant_send_queue, assistant_receive_queue))

    game_process.start()
    assistant_process.start()

    game_process.join()
    assistant_process.join()