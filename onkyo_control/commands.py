from collections import OrderedDict
import re

from serial_protocol.events import Event

START_MESSAGE = b'!'
RECEIVER_TYPE = b'1'
END_MESSAGE = b'\x0d\x0a'
EOF = b'\x1a'


_MESSAGES = OrderedDict()


def get_event_for(data, requests):
    code = data[2:5]

    if code not in _MESSAGES:
        return None, None
    
    message = _MESSAGES[code](data)

    for request in requests:
        if request.code == code:
            break
    else:
        request = None
    
    return message, request


class _Message:
    
    def __init__(self, data):
        self.data = data
    
    def parse(self):
        m = self.matcher.match(self.data)
        return m.group('status')


class MessageMeta(type):

    def __new__(cls, name, bases, dct):
        base_message_class = _Message
        message_class = dct.get('Message', None)
        
        if message_class is None:
            for base in bases:
                if hasattr(base, 'Message'):
                    base_message_class = base.Message

            message_class = dct['Message'] = \
                type('Message', (base_message_class,), {})

        klass = type.__new__(cls, name, bases, dct)
        
        if klass.code:
            message_expr = b'^%b%b(?P<code>%b)(?P<status>.*?)%b$' % (
                START_MESSAGE, RECEIVER_TYPE, klass.code, EOF)
            message_class.matcher = re.compile(message_expr)
            message_class.request_type = klass
            _MESSAGES[klass.code] = message_class

            for action, code in klass.direct.items():
                def initializer(code):
                    return lambda cls: cls(code)
                
                setattr(klass, action, classmethod(initializer(code)))

        return klass


class OnkyoEvent(Event, metaclass=MessageMeta):
    code = None
    direct = {}

    def __init__(self, value=b'QSTN'):
        self.timeout = 1.0
        self.value = value
    
    def value_as_bytes(self):
        return self.value

    def to_bytes(self):
        value = self.value_as_bytes()
        return b'%b%b%b%b%b' % (
            START_MESSAGE, RECEIVER_TYPE, self.code, value, END_MESSAGE)


class HexValueMixin:

    def value_as_bytes(self):
        if isinstance(self.value, int):
            return f'{self.value:X}'.encode('ascii')
        return super().value_as_bytes()
    
    class Message(_Message):

        def parse(self):
            status = super().parse(self)
            return int(status, base=16)


class Power(OnkyoEvent):
    code = b'PWR'
    direct = dict(
        on=b'01',
        off=b'00')


class Mute(OnkyoEvent):
    code = b'AMT'
    direct = dict(
        toggle=b'TG')


class Volume(HexValueMixin, OnkyoEvent):
    code = b'MVL'
    direct = dict(
        up=b'UP',
        down=b'DOWN')


class SleepTimer(HexValueMixin, OnkyoEvent):
    code = b'SLP'
    direct = dict(
        off=b'OFF',
        up=b'UP')


class DisplayDim(OnkyoEvent):
    code = b'DIM'
    direct = dict(
        bright=b'00',
        dim=b'01',
        dark=b'02',
        off=b'08',
        toggle=b'TG')


class OSD(OnkyoEvent):
    code = b'OSD'
    direct = dict(
        menu=b'MENU',
        up=b'UP',
        down=b'DOWN',
        right=b'RIGHT',
        left=b'LEFT',
        enter=b'ENTER',
        exit=b'EXIT')


class SelectInput(OnkyoEvent):
    code = b'SLI'
    direct = dict(
        vcr_dvr=b'00',
        cbl_sat=b'01',
        game=b'02',
        aux1=b'03',
        aux2=b'04',
        dvd=b'10',
        tape=b'20',
        phono=b'22',
        cd=b'23',
        fm=b'24',
        am=b'25',
        tuner=b'tuner',
        up=b'UP',
        down=b'DOWN')


class AudioSelect(OnkyoEvent):
    code = b'SLA'
    direct = dict(
        auto=b'00',
        mch=b'01',
        analog=b'02',
        hdmi=b'04',
        toggle=b'UP')


class ListeningMode(OnkyoEvent):
    code = b'LMD'
    direct = dict(
        stereo=b'00',
        direct=b'01',
        surround=b'02',
        thx=b'04',
        mono_movie=b'07',
        orchestra=b'08',
        unplugged=b'09',
        studio=b'0A',
        tv_logic=b'0B',
        all_ch_stereo=b'0C',
        theater_dimensional=b'0D',
        mono=b'0F',
        pure_audio=b'11',
        full_mono=b'13',
        straight=b'40',
        thx_cinema=b'42',
        thx_surround_ex=b'43',
        thx_ultra=b'50',
        thx_music=b'51',
        thx_games=b'52',
        pl2_movie=b'80',
        pl2_music=b'81',
        neo6_cinema=b'82',
        neo6_music=b'83',
        pl2_thx_cinema=b'84',
        neo6_thx_cinema=b'85',
        pl2_game=b'86',
        neural_thx=b'88',
        pl2_thx_game=b'8A',
        up=b'UP',
        down=b'DOWN',
        movie_toggle=b'MOVIE',
        music_toggle=b'MUSIC',
        game_toggle=b'GAME',
        thx_toggle=b'THX',
        auto=b'AUTO',
        surround_toggle=b'SURR',
        stereo_toggle=b'STEREO',
    )


class ReEQ(OnkyoEvent):
    code = b'RAS'
    direct = dict(
        on=b'00',
        off=b'01',
        toggle=b'UP')
