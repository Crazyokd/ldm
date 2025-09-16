#!/usr/bin/python3
import unittest

from protocol_adapter.srp_wrapper import SrpWrapper


class SrpWrapperTest(unittest.TestCase):
    def test_parse_dmcode(self):
        match0 = ('T18678632', 0, 0, 0)
        match1 = ('T1867862X', 2, 0, -0.1)
        match2 = ('T186d862c', -20, 6, 1.1)
        match3 = ('T186d862c', -20, 7, 1.7)
        match4 = (' == ', 0, 0, 0)
        match5 = ('', 0, 0, 0)

        dmcode_list = [
            # 最基础的版本
            ('T18678632(0.2, -0.3, 0)', match0),
            # 带空格，座标，单位，正负
            ('T18678632 ( 0.2 , -0.3 , -0 ) ', match0),
            ('T18678632 ( 0.2 , -0.3 , -0 deg ) ', match0),
            ('T18678632 ( 0.2 , -0.3 , -0 rad ) ', match0),
            ('T18678632(0.2mm, -0.3mm, 0°)', match0),
            ('T1867862X (2, 0.4, -0.1) ', match1),
            ('T1867862X(2mm, 0.4mm, -0.1°)', match1),
            ('T1867862X(2mm, 0.4mm, -0.1 ° )', match1),
            ('T1867862X(2mm, 0.4mm, -0.1deg )', match1),
            ('T1867862X(2mm, 0.4mm, -0.1 deg )', match1),
            # round() 银行家舍入，0.5 看整数部分奇数偶数
            ('T186d862c(-20.4mm, 5.5mm, 1.1deg )', match2),
            ('T186d862c(-20.4mm, 5.6mm, 1.1deg )', match2),
            ('T186d862c(-20.4mm, 6.4mm, 1.1deg )', match2),
            ('T186d862c(-20.4mm, 6.5mm, 1.1deg )', match2),
            ('T186d862c(-20.4mm, 6.6mm, 1.7deg )', match3),
            # dmcode 不对，原样返回，其他为 0
            (' == ', match4),
            ('', match5),
        ]

        wrapper = SrpWrapper()
        for text, match in dmcode_list:
            info = wrapper.parse_dmcode_info(text)
            print(f'>> test dmcode: [{text}]')
            self.assertEqual(info, match)

        wrapper.stop()


if __name__ == '__main__':
    unittest.main()
