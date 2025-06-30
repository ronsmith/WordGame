from unittest import TestCase, main
from play import game_state

EMPTY_SET = set()

class TestGameState(TestCase):
    
    def test_banjo(self):
        self._test('BANJO', (
            ('PIANO', 'BBYYG', {'O',}, {'A','N',}, {'P','I'}, 'playing'),
            ('ARNXO', 'YBGBG', {'N','O',}, {'A',}, {'P','I','R','X'}, 'playing'),
            ('FANDO', 'BGGBG', {'A','N','O'}, EMPTY_SET, {'D','F','I','P','R','X'}, 'playing'),
            ('JANBO', 'YGGYG', {'A','N','O'}, {'B','J'}, {'D','F','I','P','R','X'}, 'playing'),
            ('BANJO', 'GGGGG', {'B','A','N','J','O'}, EMPTY_SET, {'D','F','I','P','R','X'}, 'win')
        ))

    def test_llama(self):
        self._test('LLAMA', (
            ('SPEED', 'BBBBB', EMPTY_SET, EMPTY_SET, {'D','E','P','S'}, 'playing'),
            ('BLEST', 'BGBBB', {'L',}, EMPTY_SET, {'B','D','E','P','S','T'}, 'playing'),
            ('FALLS', 'BYYYB', {'L',}, {'A',}, {'B','D','E','F','P','S','T'}, 'playing'),
            ('MALAZ', 'YYYYB', {'L',}, {'A','M'}, {'B','D','E','F','P','S','T','Z'}, 'playing'),
            ('ALALM', 'YGGYY', {'A','L',}, {'M',}, {'B','D','E','F','P','S','T','Z'}, 'playing')
        ))

    def test_fifth(self):
        self._test('FIFTH', (
            ('STAFF', 'BYBYY', EMPTY_SET, {'T','F',}, {'S','A'}, 'playing'),
            ('TIMID', 'YGBBB', {'I',}, {'T','F',}, {'S','A','M','D'}, 'playing'),
            ('BALLS', 'BBBBB', {'I',}, {'T','F',}, {'S','A','M','D','B','A','L'}, 'playing'),
            ('FFITF', 'GYYGB', {'F','I','T'}, EMPTY_SET, {'S','A','M','D','B','A','L'}, 'playing'),
            # TODO one more row
        ))

    def _test(self, word, guess_response_list):
        attempts = []
        responses = []
        for guess, colors, kbg, kby, kbb, status in guess_response_list:
            attempts.append((guess, guess == word))
            responses.append(colors)
            state = game_state(attempts, word)
            self.assertEqual(len(responses), len(state['rows']), f'Guess: {guess} has incorrect number of rows.')
            self.assertEqual(status, state['status'], f'Guess: {guess} has incorrect status.')
            for i, row in enumerate(state['rows']):
                self.assertEqual(attempts[i][0], row['word'], f'Guess: {guess}, Row {i+1} has the rong word.')
                self.assertEqual(responses[i], row['colors'], f'Guess: {guess}, Row {i+1} has incorrect colors.')
            self.assertEqual(kbg, state['keyboard']['green'], f'Guess: {guess}, Keyboard: green has incorrect letters.')
            self.assertEqual(kby, state['keyboard']['yellow'], f'Guess: {guess}, Keyboard: yellow has incorrect letters.')
            self.assertEqual(kbb, state['keyboard']['black'], f'Guess: {guess}, Keyboard: black has incorrect letters.')





if __name__ == '__main__':
    main()
