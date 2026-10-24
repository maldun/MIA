# Known risks of the SysML v2 text (not parsed by a tool)

Where a real parser is most likely to object, in order of likelihood. Each has a fallback that keeps the meaning.

| # | Construct | Where | Why it may fail | Fallback |
|---|---|---|---|---|
| 1 | `@Implementation { :>> status = ...; :>> modules = (...); }` | Architecture | The shape of the value list `("a", "b")` for a multiplicity `[0..*]` and `:>>` inside a metadata body differ a little between releases | write `modules` as one String with commas, drop `[0..*]` |
| 2 | `satisfy hlr01 by mia;` | Allocation | Older releases need `satisfy requirement hlr01 by mia;` | add the keyword `requirement` |
| 3 | `allocate hlr01 to mia.webApp.chatService;` | Allocation | The short form `allocate a to b;` is newer than the long form `allocate a to b` with `allocation def` | use `dependency hlr01 to mia.webApp.chatService;` |
| 4 | Short names `<'HLR-01'>` after `requirement def` | Requirements | Quoted short names must be unique per namespace; fine here, but tools differ in how they print them | use `<HLR01>` |
| 5 | `then done;` at the end of an action and `first start;` | Behavior | `done` and `start` are standard-library actions and must be importable (`Actions`) | add `private import Actions::*;` or end without `then done;` |
| 6 | Unnamed `transition first a accept Signal then b;` | Behavior | Some releases require a name or `accept signal : Signal` | name the transition and write `accept sig : Signal` |
| 7 | `enum def` with a `doc` before the first `enum` | Common | Order of `doc` and members | move the `doc` into a comment |
| 8 | `interface name : Def connect a.p to b.q;` | Architecture, Context | Typed interface usage with a plain `connect` list; conjugate ports must match the ends' types | drop the type (`interface name connect a.p to b.q;`) |
| 9 | `bind chat = webApp.chat;` for ports | Architecture | Binding ports of the same type is fine, but some tools want `bind` only for attributes and `connect` for ports | replace by `connect chat to webApp.chat;` |
| 10 | `verify hlr01;` in an `objective` | Allocation | Needs a requirement usage that is visible in the package; the import with `::*` of a usage may need `miaRequirements::*` spelled differently | `verify requirement hlr01 : Conversation;` |
| 11 | `private import VerificationCases::*;` and `VerdictKind` | Allocation | Name of the standard-library package/enum differs between releases | replace `return verdict : VerdictKind;` by `return verdict : Boolean;` |
| 12 | Parts without a type that carry only `doc` and metadata | Architecture | None expected (untyped part usages are allowed), but some linters warn | give the leaf parts a trivial `part def` each |

None of these changes the content of the model. Fix one at a time, reloading after each.
