import collections

INVITATION_MAP = {
    f"iclr_{year}": f"ICLR.cc/{year}/Conference/-/Blind_Submission"
    for year in range(2018, 2023)
}


##### STATUS, EVENT TYPE, METADATA #####
class EventType(object):
  MANUSCRIPT = "manuscript"
  REVIEW = "review"
  MANUSCRIPT_REVISION = "manuscript_rev"
  REVIEW_REVISION = "review_rev"
  METAREVIEW = "metareview"
  COMMENT = "comment"


class Initiator(object):
  CONFERENCE = "conference"
  AUTHOR = "author"
  REVIEWER = "reviewer"
  METAREVIEWER = "metareviewer"
  ANONYMOUS = "anonymous"
  OTHER = "other"


class PDFStatus(object):
  AVAILABLE = "available"
  DUPLICATE = "duplicate"
  FORBIDDEN = "forbidden"
  NOT_FOUND = "not_found"
  NOT_APPLICABLE = "not_applicable"


PDF_ERROR_STATUS_LOOKUP = {
    "ForbiddenError": PDFStatus.FORBIDDEN,
    "NotFoundError": PDFStatus.NOT_FOUND,
}

EVENT_FIELDS = [
    # Identifiers
    "forum_id",
    "note_id",
    "referent_id",
    "reply_to",
    "revision_index",
    # Creator info
    "initiator",
    "initiator_type",  # One of the Initiator strings
    # Date info
    "creation_date",  # 'true creation date' from OpenReview
    "mod_date",  # 'true modification date' from OpenReview
    # Event type info
    "event_type",
    "reply_to_type",
    # File info
    "json_path",
    "pdf_path",
    "pdf_status",
    "pdf_checksum",
]

Event = collections.namedtuple("Event", EVENT_FIELDS)


def get_event_type(note, conference):
  if conference == "iclr_2018":
    if 'review' in note.content:
      return EventType.REVIEW
    elif note.id == note.forum:
      return EventType.MANUSCRIPT
    elif note.referent == note.forum:
      return EventType.MANUSCRIPT_REVISION
    elif "decision" in note.content:
      return EventType.METAREVIEW
    else:
      return EventType.COMMENT
  else:
    dsds
