from unittest import TestCase, main
from play import game_state


def _test(word, guess_response_list):
    attempts = []
    for guess, response in guess_response_list:
        attempts.append((guess, guess == word))
        state = game_state(attempts, word)


class TestGameState(TestCase):
    
    def test_easy_word(self):
        word = "BANJO"



if __name__ == '__main__':
    main()
