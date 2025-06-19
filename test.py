from unittest import TestCase, main
from play import game_state


def _test(word, guess_response_list):
    attempts = []
    responses = []
    for guess, response in guess_response_list:
        attempts.append((guess, guess == word))
        state = game_state(attempts, word)
        responses.append(response)
        # TODO


class TestGameState(TestCase):
    
    def test_easy_word(self):
        _test('BANJO', (
            ('PIANO', 'BBYYG'),
            ('ARNXO', 'YBGBG'),
            ('FANDO', 'BGGBG'),
            ('JANBO', 'YGGYG'),
            ('BANJO', 'GGGGG')
        ))



if __name__ == '__main__':
    main()
