# ------------------------------------------------
# Sub-mensagens (PollOption, PollVoteSnapshot, ...)
# ------------------------------------------------

type_poll_option = {
    '1': {'type': 'str', 'name': 'name'},
    '2': {'type': 'str', 'name': 'hash'},
}

type_poll_vote_snapshot = {
    '1': {
        'type': 'message',
        'message_typedef': type_poll_option,
        'name': 'option'
    },
    '2': {'type': 'int32', 'name': 'optionVoteCount'}
}

type_poll_votes_snapshot = {
    # repeated MsgOpaqueData.PollVoteSnapshot pollVotes = 1;
    '1': {
        'type': 'message',
        'message_typedef': type_poll_vote_snapshot,
        'label': 'repeated',
        'name': 'pollVotes'
    }
}

# PollEncValue não apareceu no trecho do .proto (apenas mencionado),
# então deixo um dict vazio. Ajuste conforme sua definição real.
type_poll_enc_value = {
    # Exemplo fictício, pois não sabemos o conteúdo real.
    # '1': {'type': 'bytes', 'name': 'encryptedStuff'},
    # '2': {'type': 'str',   'name': 'someOtherField'},
}

type_event_location = {
    # message EventLocation {
    #     optional double degreesLatitude  = 1;
    #     optional double degreesLongitude = 2;
    #     optional string name            = 3;
    #     optional string address         = 4;
    #     optional string url             = 5;
    #     optional bytes  jpegThumbnail   = 6;
    # }
    '1': {'type': 'double', 'name': 'degreesLatitude'},
    '2': {'type': 'double', 'name': 'degreesLongitude'},
    '3': {'type': 'str',    'name': 'name'},
    '4': {'type': 'str',    'name': 'address'},
    '5': {'type': 'str',    'name': 'url'},
    '6': {'type': 'bytes',  'name': 'jpegThumbnail'},
}

# Mapeamento PollContentType (enum)
poll_content_type_enum = {
    'type': 'enum',
    'name': 'pollContentType',
    # Os valores do enum:
    'values': {
        0: 'UNKNOWN',
        1: 'TEXT',
        2: 'IMAGE',
    }
}

# ------------------------------------------------
# Mensagem principal: MsgOpaqueData
# ------------------------------------------------

type_whatsappmsg = {
    # message MsgOpaqueData {
    #   optional string body                   = 1;
    #   optional string caption                = 3;
    #   optional double lng                    = 5;
    #   optional bool   isLive                 = 6;
    #   optional double lat                    = 7;
    #   optional int32  paymentAmount1000      = 8;
    #   optional string paymentNoteMsgBody     = 9;
    #   optional string matchedText            = 11;
    #   optional string title                  = 12;
    #   optional string description            = 13;
    #   optional bytes  futureproofBuffer      = 14;
    #   optional string clientUrl              = 15;
    #   optional string loc                    = 16;
    #   optional string pollName               = 17;
    #   repeated PollOption pollOptions        = 18;
    #   optional uint32 pollSelectableOptionsCount = 20;
    #   optional bytes  messageSecret          = 21;
    #   optional int64  senderTimestampMs      = 22;
    #   optional string pollUpdateParentKey    = 23;
    #   optional PollEncValue encPollVote      = 24;
    #   optional bool   isSentCagPollCreation  = 28;
    #   optional PollContentType pollContentType = 42;
    #   optional PollVotesSnapshot pollVotesSnapshot = 41;
    #   optional string encReactionTargetMessageKey = 25;
    #   optional bytes  encReactionEncPayload  = 26;
    #   optional bytes  encReactionEncIv       = 27;
    #   optional bytes  botMessageSecret       = 29;
    #   optional string targetMessageKey       = 30;
    #   optional bytes  encPayload             = 31;
    #   optional bytes  encIv                  = 32;
    #   optional string eventName              = 33;
    #   optional bool   isEventCanceled        = 34;
    #   optional string eventDescription       = 35;
    #   optional string eventJoinLink          = 36;
    #   optional int64  eventStartTime         = 37;
    #   optional EventLocation eventLocation   = 38;
    #   optional int64  eventEndTime           = 40;
    #   optional string originalSelfAuthor     = 51;
    # }

    '1':  {'type': 'str',    'name': 'body'},
    '3':  {'type': 'str',    'name': 'caption'},
    '5':  {'type': 'double', 'name': 'lng'},
    '6':  {'type': 'bool',   'name': 'isLive'},
    '7':  {'type': 'double', 'name': 'lat'},
    '8':  {'type': 'int32',  'name': 'paymentAmount1000'},
    '9':  {'type': 'str',    'name': 'paymentNoteMsgBody'},
    '11': {'type': 'str',    'name': 'matchedText'},
    '12': {'type': 'str',    'name': 'title'},
    '13': {'type': 'str',    'name': 'description'},
    # futureproofBuffer é bytes no proto, mas se você preferir
    # tratar como string (base64, etc.) pode trocar. Aqui, deixo bytes:
    '14': {'type': 'bytes',  'name': 'futureproofBuffer'},

    '15': {'type': 'str',    'name': 'clientUrl'},
    '16': {'type': 'str',    'name': 'loc'},
    '17': {'type': 'str',    'name': 'pollName'},
    '18': {
        'type': 'message',
        'message_typedef': type_poll_option,
        'label': 'repeated',
        'name': 'pollOptions'
    },
    '20': {'type': 'uint32', 'name': 'pollSelectableOptionsCount'},
    '21': {'type': 'bytes',  'name': 'messageSecret'},
    '22': {'type': 'int64',  'name': 'senderTimestampMs'},
    '23': {'type': 'str',    'name': 'pollUpdateParentKey'},

    '24': {
        'type': 'message',
        'message_typedef': type_poll_enc_value,  # Ajuste se tiver a definição real
        'name': 'encPollVote'
    },
    '25': {'type': 'str',    'name': 'encReactionTargetMessageKey'},
    '26': {'type': 'bytes',  'name': 'encReactionEncPayload'},
    '27': {'type': 'bytes',  'name': 'encReactionEncIv'},

    '28': {'type': 'bool',   'name': 'isSentCagPollCreation'},
    '29': {'type': 'bytes',  'name': 'botMessageSecret'},
    '30': {'type': 'str',    'name': 'targetMessageKey'},
    '31': {'type': 'bytes',  'name': 'encPayload'},
    '32': {'type': 'bytes',  'name': 'encIv'},

    '33': {'type': 'str',    'name': 'eventName'},
    '34': {'type': 'bool',   'name': 'isEventCanceled'},
    '35': {'type': 'str',    'name': 'eventDescription'},
    '36': {'type': 'str',    'name': 'eventJoinLink'},
    '37': {'type': 'int64',  'name': 'eventStartTime'},
    '38': {
        'type': 'message',
        'message_typedef': type_event_location,
        'name': 'eventLocation'
    },
    '40': {'type': 'int64',  'name': 'eventEndTime'},

    '41': {
        'type': 'message',
        'message_typedef': type_poll_votes_snapshot,
        'name': 'pollVotesSnapshot'
    },
    '42': poll_content_type_enum,

    '51': {'type': 'str',    'name': 'originalSelfAuthor'},
}

# ------------------------------------------------
# MsgRowOpaqueData
# ------------------------------------------------

type_prot = {
    # message MsgRowOpaqueData {
    #   optional MsgOpaqueData currentMsg = 1;
    #   optional MsgOpaqueData quotedMsg  = 2;
    # }
    '1': {
        'type': 'message',
        'message_typedef': type_whatsappmsg,
        'name': 'currentMsg'
    },
    '2': {
        'type': 'message',
        'message_typedef': type_whatsappmsg,
        'name': 'quotedMsg'
    }
}
