import unittest
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from remember_me.core.emoji_encoding import EmojiEncoder, SpaceTimeCompressor

class TestEmojiEncoder(unittest.TestCase):
    def test_round_trip(self):
        """Verify that encoding and then decoding 9-trit sequences returns the original."""
        test_cases = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1],
            [1, 0, -1, 1, 0, -1, 1, 0, -1],
            [-1, 0, 1, -1, 0, 1, -1, 0, 1],
        ]
        for trits in test_cases:
            with self.subTest(trits=trits):
                encoded = EmojiEncoder.trits_to_emoji(trits)
                decoded = EmojiEncoder.emoji_to_trits(encoded)
                self.assertEqual(trits, decoded)

    def test_padding(self):
        """Verify that sequences shorter than 9 trits are padded with 0."""
        short_trits = [1, -1, 1]
        expected_decoded = [1, -1, 1, 0, 0, 0, 0, 0, 0]
        encoded = EmojiEncoder.trits_to_emoji(short_trits)
        decoded = EmojiEncoder.emoji_to_trits(encoded)
        self.assertEqual(expected_decoded, decoded)

    def test_truncation(self):
        """Verify that sequences longer than 9 trits are truncated to 9."""
        long_trits = [1] * 12
        expected_decoded = [1] * 9
        encoded = EmojiEncoder.trits_to_emoji(long_trits)
        decoded = EmojiEncoder.emoji_to_trits(encoded)
        self.assertEqual(expected_decoded, decoded)

class TestSpaceTimeCompressor(unittest.TestCase):
    def setUp(self):
        self.compressor = SpaceTimeCompressor()

    def test_quantization(self):
        """Verify quantization logic: >0.3 -> 1, <-0.3 -> -1, else 0."""
        vector = [0.4, 0.3, 0.0, -0.3, -0.4]
        expected_trits = [1, 0, 0, 0, -1]

        # We can test this by packing and then unpacking
        # pack_vector produces emojis, unpack_vector produces trits
        encoded = self.compressor.pack_vector(vector)
        decoded_trits = self.compressor.unpack_vector(encoded)

        # unpack_vector returns 9 trits per emoji, so we check the first 5
        self.assertEqual(expected_trits, decoded_trits[:5])

    def test_multi_emoji(self):
        """Verify handling of vectors longer than 9 elements."""
        # 18 elements should result in 2 emojis
        vector = [0.5] * 18
        encoded = self.compressor.pack_vector(vector)
        self.assertEqual(len(encoded), 2)

        decoded_trits = self.compressor.unpack_vector(encoded)
        self.assertEqual(len(decoded_trits), 18)
        self.assertEqual(decoded_trits, [1] * 18)

    def test_non_multiple_of_9(self):
        """Verify handling of vectors with length not multiple of 9."""
        vector = [0.5] * 5
        encoded = self.compressor.pack_vector(vector)
        self.assertEqual(len(encoded), 1)

        decoded_trits = self.compressor.unpack_vector(encoded)
        # Should be 9 trits because 1 emoji always decodes to 9 trits
        self.assertEqual(len(decoded_trits), 9)
        self.assertEqual(decoded_trits[:5], [1] * 5)
        self.assertEqual(decoded_trits[5:], [0] * 4) # padded with zeros

    def test_pack_unpack_round_trip(self):
        """Verify round trip for a random-ish vector."""
        vector = [0.9, -0.1, -0.8, 0.4, 0.0, 0.1, -0.6, 0.7, 0.8]
        expected_trits = [1, 0, -1, 1, 0, 0, -1, 1, 1]

        encoded = self.compressor.pack_vector(vector)
        decoded_trits = self.compressor.unpack_vector(encoded)

        self.assertEqual(expected_trits, decoded_trits)

if __name__ == "__main__":
    unittest.main()
