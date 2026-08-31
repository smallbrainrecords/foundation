"""Physician attestation on a Problem — the `Problem.authenticated` flag.

The flag means "a physician has vouched for this problem's current state."
It is NOT related to login authentication.

The whole rule lives in `apply_problem_authentication` below. It is derived
SERVER-SIDE from the acting user's role on every write, because the server is
the only party that knows who the actor really is. Before 2026-08-31 the macOS
app derived it across thirteen scattered sites and the results disagreed with
each other and with the server — a physician-created problem showed
"Authenticated" locally for a few seconds and then lost it on the next pull,
because `mobile_create_problem` never accepted the field at all.

Lives in its own module (not problems_app/todo_app operations) so it can be
imported by mobile_api views AND both operations modules without cycles —
same reasoning as `mutation_stamp`.

Owner decisions, 2026-08-31 — change these deliberately, not by drift:

* **`physician` ONLY.** Admin and mid-level are NOT attesting roles, which is
  a deliberate narrowing from the legacy web rule
  (`role in ('physician', 'admin')`). The consequence was put to the owner
  explicitly and accepted: an NP/PA de-authenticates a problem on their own
  patient and only a physician can restore it.
* **Any physician qualifies** — not just the patient's controlling physician.
  A covering physician's note authenticates.
* **Physician writes SET, they never clear.** There is no way for a physician
  to say "I have not reviewed this"; the manual chip is one-way (see
  `mobile_authenticate_problem`). The flag comes off only under the rule.
* **Non-physician writes clear on exactly three actions** — creating a note,
  creating a todo, flipping a todo's accomplished status. Every other
  non-physician write (labels, images, relationships, pinned vitals, document
  links, todo edits, member tags) leaves the flag untouched. The asymmetry is
  intended: those actions do not change what a physician would need to re-read.
* **Scope is ONE level** — the problem and its direct children. A todo's own
  children (comments, todo labels, members, documents attached to the todo)
  do not touch the parent problem's flag, in either direction. Encounters are
  excluded too: linking a problem to a recording does not authenticate it.
* **Deletes count as writes**, so a physician deleting a note authenticates.
* **A write touching two problems flags both** (relationship add/remove, and
  moving a todo between problems), matching how `add_problem_activity`
  already fans out over a relationship's two endpoints.
* **No activity row here.** Derived flips are silent; only the manual chip
  press writes one. Rationale is volume against value: transitions were
  measured at ~790 in 3.5 months clinic-wide, so the row count was never the
  problem — but a derived flip is already implied by the note/todo row sitting
  beside it, which names the same actor at the same instant.

Spec: `apps/mobile_api/tests/test_problem_authentication.py`.
"""
import logging

logger = logging.getLogger(__name__)

#: The only role that attests. See the module docstring before widening this —
#: admin and mid-level are excluded on purpose.
ATTESTING_ROLES = ('physician',)


def is_attesting_actor(user):
    """True when `user` is a physician.

    A user with no profile, no role, or an anonymous request is NOT attesting.
    That direction is deliberate: the failure mode of guessing wrong here is
    asserting that a doctor vouched for a problem when none did, so anything
    unrecognized falls to the non-physician side.
    """
    try:
        role = user.profile.role
    except Exception:
        return False
    return role in ATTESTING_ROLES


def apply_problem_authentication(request, *problems, non_physician_clears=False):
    """Apply the attestation rule for ONE write, to one or more problems.

    Call this from every endpoint that writes a problem or a direct child of
    one, AFTER the write has succeeded.

        physician actor          -> authenticated = True
        non-physician actor      -> authenticated = False, but ONLY when the
                                    caller passes non_physician_clears=True
        anything else            -> left exactly as it was

    `non_physician_clears=True` belongs on exactly three call sites — problem
    note create, todo create, and a todo accomplished flip. Passing it
    anywhere else widens the rule.

    Accepts `None` entries and duplicates so callers can hand over
    `todo.problem` or a relationship's two ends without pre-filtering. Writes
    only when the value actually changes, with `update_fields`, so an
    already-authenticated problem costs one comparison and no UPDATE.
    """
    user = getattr(request, 'user', None)
    if user is None:
        return

    if is_attesting_actor(user):
        target = True
    elif non_physician_clears:
        target = False
    else:
        # A non-physician write that the rule does not care about. Leaving the
        # flag alone is the whole point — do not "normalize" it here.
        return

    seen = set()
    for problem in problems:
        if problem is None or problem.pk in seen:
            continue
        seen.add(problem.pk)
        if problem.authenticated == target:
            continue
        problem.authenticated = target
        try:
            problem.save(update_fields=['authenticated'])
        except Exception:
            # Never take down a clinical write that already succeeded. A stale
            # flag is recoverable — the next write on this problem re-derives
            # it — whereas a 500 here would roll back the note or todo the
            # user actually came to save.
            logger.exception(
                'apply_problem_authentication failed for problem %s (non-fatal)',
                problem.pk,
            )
