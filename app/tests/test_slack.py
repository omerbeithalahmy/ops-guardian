import unittest
from app.services import slack

class TestSlackBlocks(unittest.TestCase):

    def test_get_remediation_blocks_with_resources(self):
        resources = [
            {"id": "vol-1", "display": "Volume vol-1", "type": "volume"},
            {"id": "vol-2", "display": "Volume vol-2", "type": "volume"}
        ]
        blocks = slack.get_remediation_blocks("costs", resources)
        
        # Verify Header (No emojis)
        self.assertEqual(blocks[0]['type'], 'header')
        self.assertNotIn("🔍", blocks[0]['text']['text'])
        self.assertIn("INVESTIGATION", blocks[0]['text']['text'])
        
        # Verify Buttons (Resolve + Cancel)
        actions_block = blocks[5]
        self.assertEqual(len(actions_block['elements']), 2)
        self.assertEqual(actions_block['elements'][0]['action_id'], "remediate_selected")
        self.assertEqual(actions_block['elements'][1]['action_id'], "cancel_to_control")

    def test_get_remediation_blocks_empty(self):
        blocks = slack.get_remediation_blocks("costs", [])
        
        # Structure changed:
        # 0: Header
        # 3: Section (Zero findings - no emojis)
        self.assertEqual(blocks[0]['type'], 'header')
        self.assertNotIn("✅", blocks[3]['text']['text'])
        self.assertIn("Zero findings", blocks[3]['text']['text'])
        self.assertEqual(blocks[4]['elements'][0]['action_id'], "cancel_to_control")

if __name__ == '__main__':
    unittest.main()
