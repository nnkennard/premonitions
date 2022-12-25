import argparse
import collections
import hashlib
import json
import openreview
import tqdm

from openreview_lib import EventType, Initiator, PDFStatus, Event
from openreview_lib import INVITATION_MAP, PDF_ERROR_STATUS_LOOKUP

import openreview_lib as orl

parser = argparse.ArgumentParser(description="")
parser.add_argument("-o", "--output_dir", default="", type=str, help="")
parser.add_argument("-f", "--offset", default=0, type=int, help="")
parser.add_argument("-c",
                    "--conference",
                    choices=INVITATION_MAP.keys(),
                    help="")


BATCH_SIZE = 10
GUEST_CLIENT = openreview.Client(baseurl="https://api.openreview.net")


##### HELPERS #####
def make_path(directories, filename=None):
  directory = os.path.join(*directories)
  os.makedirs(directory, exist_ok=True)
  if filename is not None:
    return os.path.join(*directories, filename)


def get_sorted_references(note):
  return [note] + sorted(
      GUEST_CLIENT.get_references(referent=note.id, original=True),
      key=lambda x: x.tcdate,
  )


def clean_timestamp(timestamp):
  return datetime.fromtimestamp(int(timestamp /
                                    1000)).strftime("%m/%d/%Y, %H:%M:%S")


def get_initiator(note):
  initiator = "|".join([s.split("/")[-1] for s in note.signatures])
  if 'Conference' in initiator:
    initiator_type = Initiator.CONFERENCE
  return initiator, initiator_type

def get_manuscript_base_path(output_dir, forum):
  return f'{output_dir}/{forum}'


##### PRODUCE DATA #####
# submissions and revisions
def write_artifact(
    revision, 
    revision_index,
    manuscript_base_path,
    checksum_to_path,
    ):

  is_reference = revision_index == 0
  pdf_path = f'{manuscript_base_path}__{revision_index}.pdf'
  json_path = f'{manuscript_base_path}__{revision_index}.json'
  with open(json_path, 'w') as f:
    json.dump(revision.to_json(), f)

  this_checksum = None
  try:  # try to get the PDF for this submission or revision
    pdf_binary = GUEST_CLIENT.get_pdf(revision.id, is_reference=is_reference)
    this_checksum = hashlib.md5(pdf_binary).hexdigest()
    if this_checksum in checksum_to_path:
      pdf_path = checksum_to_path[this_checksum]
      pdf_status = PDFStatus.DUPLICATE
    else:
      pdf_status = PDFStatus.AVAILABLE
      checksum_to_path[this_checksum] = pdf_path
      with open(pdf_path, "wb") as file_handle:
        file_handle.write(pdf_binary)
  except openreview.OpenReviewException as e:
    pdf_path = "N/A"
    pdf_status = PDF_ERROR_STATUS_LOOKUP[e.args[0]["name"]]

  return pdf_status, this_checksum

def get_paper_paths(forum, revision_index, output_dir):
  path_base = f'{output_dir}/{forum}__{revision_index}'
  return f'{path_base}.json', f'{path_base}.pdf'


def process_manuscript_and_revisions(forum_note, conference, output_dir):

  forum = forum_note.forum
  original = forum_note.original

  checksum_to_path = {}
  events = []

  for revision_index, revision in enumerate(get_sorted_references(forum_note)):
    if revision.id == original:
      continue
    initiator, initiator_type = get_initiator(revision)

    manuscript_base_path = get_manuscript_base_path(output_dir, forum)

    pdf_status, checksum = write_artifact(revision, revision_index,
        manuscript_base_path, checksum_to_path)

    events.append(
        Event(
            forum_id=forum,
            note_id=revision.id,
            referent_id=revision.referent,
            reply_to=None,
            revision_index=revision_index,
            initiator=initiator,
            initiator_type=initiator_type,
            creation_date=revision.tcdate,
            mod_date=revision.tmdate,
            event_type=orl.get_event_type(revision, conference),
            reply_to_type=None,
            json_path=f'{manuscript_base_path}__{revision_index}.json',
            pdf_path=checksum_to_path.get(checksum, None),
            pdf_status=pdf_status,
            pdf_checksum=checksum,
        ))

  return events


def main():
  args = parser.parse_args()
  assert args.conference in INVITATION_MAP

  # Get all 'forum' notes for the conference, filter if necessary
  forum_notes = list(
      openreview.tools.iterget_notes(
          GUEST_CLIENT, invitation=INVITATION_MAP[args.conference]))

  events = []
  #for i in tqdm.tqdm(range(args.offset, len(forum_notes), BATCH_SIZE)):
  for i in tqdm.tqdm(range(args.offset, 20, BATCH_SIZE)):
    forum_notes_subset = forum_notes[i:i + BATCH_SIZE]
    page_number = str(int(i / BATCH_SIZE)).zfill(4)

    for forum_note in tqdm.tqdm(forum_notes_subset):
      events += process_manuscript_and_revisions(forum_note, args.conference,
          args.output_dir)
      
  for i in events:
    print("\t".join(str(j) for j in i._asdict().values()))

if __name__ == "__main__":
  main()
