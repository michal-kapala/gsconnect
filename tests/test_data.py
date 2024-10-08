import sys, os, unittest
# relative module import stuff
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_dir)
from data import List, Bin

class DataTests(unittest.TestCase):
  """Tests for data parsing and other utilities."""
  def test_serialize_outer_dl(self):
    list = List([['xd'],'ddd'])
    self.assertEqual(list.to_buf(), bytes([0x5B, 0x73, 0x78, 0x64, 0x00, 0x5D, 0x73, 0x64, 0x64, 0x64, 0x00]))

  def test_serialize_inner_dl(self):
    list = List([['xd'],'ddd'])
    self.assertEqual(list.to_buf(False), bytes([0x5B, 0x5B, 0x73, 0x78, 0x64, 0x00, 0x5D, 0x73, 0x64, 0x64, 0x64, 0x00, 0x5D]))

  def test_deserialize_outer_dl(self):
    input = bytearray([0x73, 0x32, 0x00, 0x73, 0x31, 0x00, 0x73, 0x31, 0x00, 0x5B, 0x5D])
    list = List.from_buf(input)
    self.assertEqual(list.lst, ['2', '1', '1', []])

  def test_deserialize_inner_dl(self):
    input = bytearray([0x5B, 0x73, 0x32, 0x00, 0x73, 0x31, 0x00, 0x73, 0x31, 0x00, 0x5B, 0x5D, 0x5D])
    list = List.from_buf(input, False)
    self.assertEqual(list.lst, ['2', '1', '1', []])

  def test_serialize_bin(self):
    input = b'Hello'
    bin = bytes(Bin(input))
    self.assertEqual(bin, b'b\x00\x00\x00\x05\x48\x65\x6C\x6C\x6F')

  def test_deserialize_bin(self):
    input = b'b\x00\x00\x00\x05\x48\x65\x6C\x6C\x6F'
    bin = Bin.from_buf(bytearray(input))
    self.assertEqual(bin.bts, b'Hello')

if __name__ == '__main__':
  unittest.main()
