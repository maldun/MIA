# Manual phone checklist for the chat page

Do this once on a real phone (and again after bigger changes). Open MIA's page over the HTTPS port (see `ui/README.md`, "HTTPS for other devices").
Automatic checks cannot replace this: the on-screen keyboard, touch gestures and real speech output need a real device.

## Layout and keyboard
- [ ] The character fills the screen, the chat is a sheet at the bottom; the whole figure is visible above the sheet, the head is not under the mood line.
- [ ] Drag the handle: the sheet snaps to peek, half and full; the character moves and shrinks smoothly to stay in the free area.
- [ ] Tap the field: the keyboard opens, the sheet sits above it, the field is not covered; closing the keyboard restores the sheet.
- [ ] Turn the phone to landscape: the chat becomes a panel at the right, the character stays centered in the free area. Turn back.
- [ ] Hide the chat (arrow in the header): the character gets the whole screen, the round chat button appears at the bottom.

## Conversation
- [ ] Enter inserts a new line, the send button sends. (Settings: "Enter key" can change this.)
- [ ] An answer streams in, the typing dots appear first, the stop button appears while MIA answers and the answer stays when you stop it.
- [ ] With the chat hidden, MIA's answer appears as a caption and fades out.
- [ ] Write a second message while MIA is answering: it waits ("Waiting") and is sent afterwards.
- [ ] Switch to flight mode for a moment: the banner "Connection lost" appears, sending is disabled, the draft stays; back online, missed messages appear.
- [ ] Reload the page: the history is there, scrolled to the bottom; scroll up loads older messages without jumping.
- [ ] `/` in the field opens the command list; `/break!` asks before it runs (cancel it).
- [ ] A message sent from the phone shows up on the computer and the other way round.

## Sound and character
- [ ] The first time: "Tap to enable sound" appears when the browser blocks autoplay; tapping it plays MIA's voice; the mouth moves while she speaks.
- [ ] Menu: mute and volume work; camera (body, bust, face) changes the view; the background list appears when there are pictures.
- [ ] Pinch zooms and one finger turns the character in the free area; the chat sheet still scrolls on its own.

## Look and accessibility
- [ ] Dark, light and auto theme look right; the system dark mode switches "Auto".
- [ ] All buttons are easy to hit (at least 44 x 44 px).
- [ ] Text size set to large in the phone's settings: nothing is cut off, no sideways scrolling.
- [ ] Screen reader (TalkBack or VoiceOver): a finished answer is read once, not word by word; buttons have names.
- [ ] Settings (menu): compact messages, times, emotions and the mood line can be switched; "Reset settings" restores everything.
