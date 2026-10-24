/*
 * Number gate, stability and baselines (Plan iteration 1 of MIA, specs/number-gate/requirements.md).
 * Views of one model: functions, parts with the agent view, allocation, deployment, requirements, verification.
 * Part of the system-wide model in specs/mia/architecture.sysml: VerificationGate, NumberCheck and the steps refine
 * mia.verifier.hardChecks and mia.verifier.verificationStyles; Harness and StabilityMetric refine mia.evaluation.harness.
 */
package NumberGate {
    private import ScalarValues::*;

    // ---------------------------------------------------------------
    // Annotations for the agent view (agent-app conventions, section 8)
    // ---------------------------------------------------------------
    package Annotations {
        metadata def ModelStep {
            attribute schema : String;
            attribute tools : String;
            attribute tokenBudget : Integer;
            attribute secondBudget : Real;
            attribute pin : String;
            attribute criterion : String;
        }
        metadata def Untrusted { attribute origin : String; }
        metadata def TrustBoundary {
            attribute boundary : String;
            attribute threats : String;
        }
    }

    // ---------------------------------------------------------------
    // What flows
    // ---------------------------------------------------------------
    package Items {
        private import Annotations::*;
        private import ScalarValues::*;

        item def Claim {
            @Untrusted { origin = "model"; }
            doc /* One statement to verify; it comes from a draft answer or from a suite. */
            attribute text : String;
        }
        item def Evidence {
            @Untrusted { origin = "web"; }
            doc /* Source passages for the claim (Wikipedia text in VitaminC); after preparation at most 4000 characters plus the check line (REQ-GATE-005). */
            attribute text : String;
        }
        item def CheckResult {
            attribute status : String;      // pass | fail | inconclusive | not_applicable (IF-001)
            attribute detail : String;
        }
        item def Arguments { doc /* 1 to 4 points of 3 to 400 characters (REQ-ARG-001). */ }
        item def Ruling {
            attribute verdict : String;     // supported | refuted | unclear (IF-002)
            attribute reason : String;
            attribute confidence : Real;
        }
        item def Verdict { attribute status : String; }
        item def Fact { doc /* A triple: normalised entity, number with unit, hash of the anchored quote (glossary). */ }
        item def CaseInput { doc /* One case for the gate: claim, evidence, and the seed and temperature of the pin (IF-005). */ }
        item def ClaimResult {
            attribute verdict : String;
            attribute calls : Integer;
            attribute seconds : Real;
            doc /* Result record of one run of one case, with the facts of the answer if it has any (IF-003). */
        }
        item def ModelPin {
            attribute name : String;
            attribute digest : String;
            attribute seed : Integer;
            attribute temperature : Real;
        }
        item def SuiteFiles { doc /* eval/suites/<name>/ with cases.jsonl and suite.json; retired cases are skipped (REQ-EVAL-002). */ }
        item def CaseList { doc /* Active cases of a suite, optionally a seeded sample that keeps pairs together (REQ-EVAL-004). */ }
        item def RunHeader { doc /* Versions, pin, seed, temperature, repeats and the SHA-1 of each suite file (REQ-EVAL-001). */ }
        item def RunRecords { doc /* Per case and repeat: status, verdict, facts, calls, seconds (IF-004). */ }
        item def StabilityReport {
            attribute shareStable : Real;
            doc /* Share of stable cases, Wilson 95 percent interval and the identifiers of the unstable cases (REQ-STAB-002). */
        }
        item def FetchedPage { @Untrusted { origin = "web"; } doc /* The cleaned text of a page fetched by the lookup. */ }
        item def ContentHash { attribute value : String; }
    }

    // ---------------------------------------------------------------
    // Functional view
    // ---------------------------------------------------------------
    package Functions {
        private import Items::*;

        action def ReceiveClaim { out item claim : Claim; out item evidence : Evidence; }
        action def CheckNumber { in item claim : Claim; in item evidence : Evidence; out item check : CheckResult; }
        action def PrepareEvidence { in item evidence : Evidence; in item check : CheckResult; out item prepared : Evidence; }
        action def ArgueFor { in item claim : Claim; in item prepared : Evidence; out item points : Arguments; }
        action def ArgueAgainst { in item claim : Claim; in item prepared : Evidence; out item points : Arguments; }
        action def JudgeClaim {
            in item claim : Claim;
            in item prepared : Evidence;
            in item pro : Arguments;
            in item con : Arguments;
            out item ruling : Ruling;
        }
        action def JudgeSingle { in item claim : Claim; in item prepared : Evidence; out item ruling : Ruling; }
        action def CombineVerdict { in item check : CheckResult; in item ruling : Ruling; out item verdict : Verdict; }

        action def VerifyClaim {
            doc /* One claim from receipt to verdict. A failed number check ends here (REQ-GATE-002); a claim without a number takes the single voice (REQ-GATE-004); the cops steps run otherwise (REQ-GATE-003). */
            action receiveClaim : ReceiveClaim;
            action checkNumber : CheckNumber;
            action prepareEvidence : PrepareEvidence;
            action argueFor : ArgueFor;
            action argueAgainst : ArgueAgainst;
            action judgeClaim : JudgeClaim;
            action judgeSingle : JudgeSingle;
            action combineVerdict : CombineVerdict;
            flow from receiveClaim.claim to checkNumber.claim;
            flow from receiveClaim.evidence to checkNumber.evidence;
            flow from receiveClaim.evidence to prepareEvidence.evidence;
            flow from checkNumber.check to prepareEvidence.check;
            flow from receiveClaim.claim to argueFor.claim;
            flow from prepareEvidence.prepared to argueFor.prepared;
            flow from receiveClaim.claim to argueAgainst.claim;
            flow from prepareEvidence.prepared to argueAgainst.prepared;
            flow from receiveClaim.claim to judgeClaim.claim;
            flow from prepareEvidence.prepared to judgeClaim.prepared;
            flow from argueFor.points to judgeClaim.pro;
            flow from argueAgainst.points to judgeClaim.con;
            flow from receiveClaim.claim to judgeSingle.claim;
            flow from prepareEvidence.prepared to judgeSingle.prepared;
            flow from checkNumber.check to combineVerdict.check;
            flow from judgeClaim.ruling to combineVerdict.ruling;
            flow from judgeSingle.ruling to combineVerdict.ruling;
        }
        action verifyClaim : VerifyClaim;

        // measurement
        action def ReadSuite { out item suite : SuiteFiles; }
        action def ReadPin { out item pin : ModelPin; }
        action def SelectCases { in item suite : SuiteFiles; out item cases : CaseList; }
        action def DispatchCases { in item cases : CaseList; in item pin : ModelPin; out item caseInput : CaseInput; }
        action def DecideCase { in item caseInput : CaseInput; out item result : ClaimResult; }
        action def CollectResults { in item result : ClaimResult; in item pin : ModelPin; out item records : RunRecords; }
        action def RecordRun { in item records : RunRecords; in item pin : ModelPin; out item header : RunHeader; }
        action def ExtractFacts { in item records : RunRecords; out item facts : RunRecords; }
        action def ComparePairs { in item facts : RunRecords; out item report : StabilityReport; }
        action def MeasureSuite {
            doc /* From a suite to the run file and the stability report. The harness reads the suite and the pin, dispatches each active case with the seed and temperature, the gate decides it (decideCase stands for verifyClaim as a whole), the harness collects the results. */
            action readSuite : ReadSuite;
            action readPin : ReadPin;
            action selectCases : SelectCases;
            action dispatchCases : DispatchCases;
            action decideCase : DecideCase;
            action collectResults : CollectResults;
            action recordRun : RecordRun;
            action extractFacts : ExtractFacts;
            action comparePairs : ComparePairs;
            flow from readSuite.suite to selectCases.suite;
            flow from selectCases.cases to dispatchCases.cases;
            flow from readPin.pin to dispatchCases.pin;
            flow from readPin.pin to collectResults.pin;
            flow from readPin.pin to recordRun.pin;
            flow from dispatchCases.caseInput to decideCase.caseInput;
            flow from decideCase.result to collectResults.result;
            flow from collectResults.records to recordRun.records;
            flow from collectResults.records to extractFacts.records;
            flow from extractFacts.facts to comparePairs.facts;
        }
        action measureSuite : MeasureSuite;

        // sources of a lookup (REQ-STAB-003)
        action def StorePage { in item page : FetchedPage; out item hash : ContentHash; }
        action storePage : StorePage;
    }

    // ---------------------------------------------------------------
    // Logical architecture with the agent view
    // ---------------------------------------------------------------
    package Structure {
        private import Items::*;
        private import Annotations::*;

        port def ClaimPort { out item claim : Claim; }
        port def EvidencePort { out item evidence : Evidence; }
        port def CheckPort { out item check : CheckResult; }
        port def ArgumentsPort { out item points : Arguments; }
        port def RulingPort { out item ruling : Ruling; }
        port def ResultPort { out item result : ClaimResult; }
        port def RecordsPort { out item records : RunRecords; }
        port def ReportPort { out item report : StabilityReport; }
        port def PagePort { out item page : FetchedPage; }
        port def CasePort { out item caseInput : CaseInput; }

        part def VerificationGate {
            doc /* Code (verification.py, checks.py, library/pipelines): classifies the claim, calls the number check, prepares the evidence (check line, 4000-character limit), runs the single voice or the cops steps, tallies the ruling. Owns the run budget. */
            port claimOut : ClaimPort;
            port evidenceOut : EvidencePort;
            port checkIn : ~CheckPort;
            port rulingIn : ~RulingPort;
            port caseIn : ~CasePort;
            port resultOut : ResultPort;
        }
        part def NumberCheck {
            doc /* Code (checks.py): numbers with units from claim and evidence, the agreement rule with the rounding cap, bounds. */
            port claimIn : ~ClaimPort;
            port evidenceIn : ~EvidencePort;
            port checkOut : CheckPort;
        }
        part def ArgueStep {
            doc /* Model step view.argue@1: points for or against the claim, from the evidence only. */
            @ModelStep { schema = "view.argue@1 output schema"; tools = ""; tokenBudget = 2500; secondBudget = 2.0; pin = "MP-light"; criterion = "REQ-VER-001, REQ-VER-002"; }
            @TrustBoundary { boundary = "TB-evidence"; threats = "THR-001, THR-002, THR-003"; }
            port claimIn : ~ClaimPort;
            port evidenceIn : ~EvidencePort;
            port pointsOut : ArgumentsPort;
        }
        part def JudgeStep {
            doc /* Model step view.judge@1: reads claim, evidence and both sides and rules. */
            @ModelStep { schema = "view.judge@1 output schema"; tools = ""; tokenBudget = 4500; secondBudget = 3.0; pin = "MP-light"; criterion = "REQ-VER-001, REQ-VER-002, REQ-VER-003, REQ-VER-004, REQ-VER-007"; }
            @TrustBoundary { boundary = "TB-evidence"; threats = "THR-001, THR-002, THR-003"; }
            port claimIn : ~ClaimPort;
            port evidenceIn : ~EvidencePort;
            port proIn : ~ArgumentsPort;
            port conIn : ~ArgumentsPort;
            port rulingOut : RulingPort;
        }
        part def SingleVoiceStep {
            doc /* Model step view.verdict@1 (pipeline verify.single@1): one voice, claim and evidence only; the current release for claims without a number. */
            @ModelStep { schema = "view.verdict@1 output schema"; tools = ""; tokenBudget = 3000; secondBudget = 1.5; pin = "MP-light"; criterion = "REQ-VER-001, REQ-VER-002, REQ-VER-003, REQ-VER-004"; }
            @TrustBoundary { boundary = "TB-evidence"; threats = "THR-001, THR-002, THR-003"; }
            port claimIn : ~ClaimPort;
            port evidenceIn : ~EvidencePort;
            port rulingOut : RulingPort;
        }
        part def Harness {
            doc /* Code (harness.py, tools/eval.py): selects the active cases of a suite, runs them with the pin, records the run with its header. */
            port resultIn : ~ResultPort;
            port caseOut : CasePort;
            port recordsOut : RecordsPort;
        }
        part def StabilityMetric {
            doc /* Code (metrics.py): reduces the answer of each repeat to its facts, compares the repeats of a case, reports share, interval and unstable cases. */
            port recordsIn : ~RecordsPort;
            port reportOut : ReportPort;
        }
        part def LookupPipeline {
            doc /* Code (research.py, content_store.py): fetches pages and stores each by its hash. Existing; REQ-STAB-003 only states the rule. */
            port pageOut : PagePort;
        }
    }

    package System {
        private import Items::*;
        private import Structure::*;

        part def NumberGateSystem {
            part gate : VerificationGate;
            part numberCheck : NumberCheck;
            part proArguer : ArgueStep;
            part conArguer : ArgueStep;
            part judge : JudgeStep;
            part singleVoice : SingleVoiceStep;
            part harness : Harness;
            part stability : StabilityMetric;
            part lookup : LookupPipeline;
            flow of Claim from gate.claimOut to numberCheck.claimIn;
            flow of Evidence from gate.evidenceOut to numberCheck.evidenceIn;
            flow of CheckResult from numberCheck.checkOut to gate.checkIn;
            flow of Claim from gate.claimOut to proArguer.claimIn;
            flow of Evidence from gate.evidenceOut to proArguer.evidenceIn;
            flow of Claim from gate.claimOut to conArguer.claimIn;
            flow of Evidence from gate.evidenceOut to conArguer.evidenceIn;
            flow of Claim from gate.claimOut to judge.claimIn;
            flow of Evidence from gate.evidenceOut to judge.evidenceIn;
            flow of Arguments from proArguer.pointsOut to judge.proIn;
            flow of Arguments from conArguer.pointsOut to judge.conIn;
            flow of Ruling from judge.rulingOut to gate.rulingIn;
            flow of Claim from gate.claimOut to singleVoice.claimIn;
            flow of Evidence from gate.evidenceOut to singleVoice.evidenceIn;
            flow of Ruling from singleVoice.rulingOut to gate.rulingIn;
            flow of CaseInput from harness.caseOut to gate.caseIn;
            flow of ClaimResult from gate.resultOut to harness.resultIn;
            flow of RunRecords from harness.recordsOut to stability.recordsIn;
        }
        part numberGate : NumberGateSystem;
    }

    // ---------------------------------------------------------------
    // Allocation and deployment
    // ---------------------------------------------------------------
    package Allocation {
        private import Functions::*;
        private import System::*;
        allocation def FunctionToPart;
        allocation : FunctionToPart allocate verifyClaim.receiveClaim to numberGate.gate;
        allocation : FunctionToPart allocate verifyClaim.prepareEvidence to numberGate.gate;
        allocation : FunctionToPart allocate verifyClaim.combineVerdict to numberGate.gate;
        allocation : FunctionToPart allocate verifyClaim.checkNumber to numberGate.numberCheck;
        allocation : FunctionToPart allocate verifyClaim.argueFor to numberGate.proArguer;
        allocation : FunctionToPart allocate verifyClaim.argueAgainst to numberGate.conArguer;
        allocation : FunctionToPart allocate verifyClaim.judgeClaim to numberGate.judge;
        allocation : FunctionToPart allocate verifyClaim.judgeSingle to numberGate.singleVoice;
        allocation : FunctionToPart allocate measureSuite.readSuite to numberGate.harness;
        allocation : FunctionToPart allocate measureSuite.readPin to numberGate.harness;
        allocation : FunctionToPart allocate measureSuite.selectCases to numberGate.harness;
        allocation : FunctionToPart allocate measureSuite.dispatchCases to numberGate.harness;
        allocation : FunctionToPart allocate measureSuite.decideCase to numberGate.gate;
        allocation : FunctionToPart allocate measureSuite.collectResults to numberGate.harness;
        allocation : FunctionToPart allocate measureSuite.recordRun to numberGate.harness;
        allocation : FunctionToPart allocate measureSuite.extractFacts to numberGate.stability;
        allocation : FunctionToPart allocate measureSuite.comparePairs to numberGate.stability;
        allocation : FunctionToPart allocate storePage to numberGate.lookup;
    }

    package Deployment {
        private import System::*;
        part def ExecutionNode { attribute host : String; }
        part def ModelServer {
            attribute server : String;
            attribute pins : String;
        }
        part miaProcess : ExecutionNode { :>> host = "MIA process (Python, CPU) on the development host; harness runs in it"; }
        part ollamaServer : ModelServer { :>> server = "Ollama in podman, ollama/ollama:rocm, RX 7800 XT 16 GB, one model, one slot"; :>> pins = "MP-light"; }
        allocation def DeployedOn;
        allocation : DeployedOn allocate numberGate.gate to miaProcess;
        allocation : DeployedOn allocate numberGate.numberCheck to miaProcess;
        allocation : DeployedOn allocate numberGate.harness to miaProcess;
        allocation : DeployedOn allocate numberGate.stability to miaProcess;
        allocation : DeployedOn allocate numberGate.lookup to miaProcess;
        allocation : DeployedOn allocate numberGate.proArguer to ollamaServer;
        allocation : DeployedOn allocate numberGate.conArguer to ollamaServer;
        allocation : DeployedOn allocate numberGate.judge to ollamaServer;
        allocation : DeployedOn allocate numberGate.singleVoice to ollamaServer;
    }

    // ---------------------------------------------------------------
    // Budgets (seconds per claim on MP-light, sequential on one model slot)
    // ---------------------------------------------------------------
    package Budgets {
        private import Structure::*;
        private import ScalarValues::*;
        part def GateTimeBudget {
            attribute gateOverhead : Real = 0.2;     // routing, evidence preparation, tally
            attribute numberCheckTime : Real = 0.1;
            attribute proArguerTime : Real = 2.0;
            attribute conArguerTime : Real = 2.0;
            attribute judgeTime : Real = 3.0;
            attribute totalLimit : Real = 10.0;      // NFR-BUD-001; the sum is 9.3 s
        }
    }

    // ---------------------------------------------------------------
    // Requirements
    // ---------------------------------------------------------------
    package Requirements {
        private import Structure::*;
        private import System::*;

        requirement def <'REQ-GATE-001'> NumberCheckFirst { subject gate : VerificationGate; }
        requirement def <'REQ-GATE-002'> FailedCheckDecides { subject gate : VerificationGate; }
        requirement def <'REQ-GATE-003'> StyleForOpenClaims { subject gate : VerificationGate; }
        requirement def <'REQ-GATE-004'> ClaimsWithoutNumber { subject gate : VerificationGate; }
        requirement def <'REQ-GATE-005'> EvidenceSizeLimit { subject gate : VerificationGate; }
        requirement def <'REQ-NUM-001'> ContradictingNumber { subject chk : NumberCheck; }
        requirement def <'REQ-NUM-002'> NoNumberInEvidence { subject chk : NumberCheck; }
        requirement def <'REQ-NUM-003'> ClaimsWithBound { subject chk : NumberCheck; }
        requirement def <'REQ-NUM-004'> NoEvidence { subject chk : NumberCheck; }
        requirement def <'REQ-NUM-005'> ScaleWordsAndUnits { subject chk : NumberCheck; }
        requirement def <'REQ-NUM-006'> QuantityMatching { subject chk : NumberCheck; }
        requirement def <'REQ-ARG-001'> StructuredArguments { subject arg : ArgueStep; }
        requirement def <'IF-001'> CheckResultInterface { subject chk : NumberCheck; }
        requirement def <'IF-002'> RulingInterface { subject jdg : JudgeStep; }
        requirement def <'IF-003'> ResultRecordInterface { subject gate : VerificationGate; }
        requirement def <'IF-004'> RunRecordsInterface { subject hrn : Harness; }
        requirement def <'IF-005'> CaseInputInterface { subject hrn : Harness; }
        requirement def <'IF-006'> SingleVoiceRulingInterface { subject sv : SingleVoiceStep; }
        requirement def <'REQ-VER-001'> WrongClaimsWithEvidence { subject gate : VerificationGate; }
        requirement def <'REQ-VER-002'> WrongClaimsWithoutEvidence { subject gate : VerificationGate; }
        requirement def <'REQ-VER-003'> TrueClaimsKeptWithEvidence { subject gate : VerificationGate; }
        requirement def <'REQ-VER-004'> TrueClaimsKeptWithoutEvidence { subject gate : VerificationGate; }
        requirement def <'REQ-VER-005'> StableVerdictsWithEvidence { subject gate : VerificationGate; }
        requirement def <'REQ-VER-006'> StableVerdictsWithoutEvidence { subject gate : VerificationGate; }
        requirement def <'REQ-VER-007'> InstructionsInEvidence { subject gate : VerificationGate; }
        requirement def <'REQ-STAB-001'> SameFactsAcrossRepeats { subject stb : StabilityMetric; }
        requirement def <'REQ-STAB-002'> StabilityReportContent { subject stb : StabilityMetric; }
        requirement def <'REQ-STAB-003'> StoredSources { subject lkp : LookupPipeline; }
        requirement def <'REQ-EVAL-001'> RunHeaderWithPin { subject hrn : Harness; }
        requirement def <'REQ-EVAL-002'> RetiredCasesSkipped { subject hrn : Harness; }
        requirement def <'REQ-EVAL-003'> SeedAndTemperatureReachModel { subject hrn : Harness; }
        requirement def <'REQ-EVAL-004'> SeededSample { subject hrn : Harness; }
        requirement def <'NFR-BUD-001'> TimePerClaim { subject gate : VerificationGate; }

        requirement reqGate001 : NumberCheckFirst;
        requirement reqGate002 : FailedCheckDecides;
        requirement reqGate003 : StyleForOpenClaims;
        requirement reqGate004 : ClaimsWithoutNumber;
        requirement reqGate005 : EvidenceSizeLimit;
        requirement reqNum001 : ContradictingNumber;
        requirement reqNum002 : NoNumberInEvidence;
        requirement reqNum003 : ClaimsWithBound;
        requirement reqNum004 : NoEvidence;
        requirement reqNum005 : ScaleWordsAndUnits;
        requirement reqNum006 : QuantityMatching;
        requirement reqArg001 : StructuredArguments;
        requirement if001 : CheckResultInterface;
        requirement if002 : RulingInterface;
        requirement if003 : ResultRecordInterface;
        requirement if004 : RunRecordsInterface;
        requirement if005 : CaseInputInterface;
        requirement if006 : SingleVoiceRulingInterface;
        requirement reqVer001 : WrongClaimsWithEvidence;
        requirement reqVer002 : WrongClaimsWithoutEvidence;
        requirement reqVer003 : TrueClaimsKeptWithEvidence;
        requirement reqVer004 : TrueClaimsKeptWithoutEvidence;
        requirement reqVer005 : StableVerdictsWithEvidence;
        requirement reqVer006 : StableVerdictsWithoutEvidence;
        requirement reqVer007 : InstructionsInEvidence;
        requirement reqStab001 : SameFactsAcrossRepeats;
        requirement reqStab002 : StabilityReportContent;
        requirement reqStab003 : StoredSources;
        requirement reqEval001 : RunHeaderWithPin;
        requirement reqEval002 : RetiredCasesSkipped;
        requirement reqEval003 : SeedAndTemperatureReachModel;
        requirement reqEval004 : SeededSample;
        requirement nfrBud001 : TimePerClaim;

        satisfy reqGate001 by numberGate.gate;
        satisfy reqGate002 by numberGate.gate;
        satisfy reqGate003 by numberGate.gate;
        satisfy reqGate004 by numberGate.gate;
        satisfy reqGate005 by numberGate.gate;
        satisfy reqNum001 by numberGate.numberCheck;
        satisfy reqNum002 by numberGate.numberCheck;
        satisfy reqNum003 by numberGate.numberCheck;
        satisfy reqNum004 by numberGate.numberCheck;
        satisfy reqNum005 by numberGate.numberCheck;
        satisfy reqNum006 by numberGate.numberCheck;
        satisfy reqArg001 by numberGate.proArguer;
        satisfy if001 by numberGate.numberCheck;
        satisfy if002 by numberGate.judge;
        satisfy if003 by numberGate.gate;
        satisfy if004 by numberGate.harness;
        satisfy if005 by numberGate.harness;
        satisfy if006 by numberGate.singleVoice;
        satisfy reqVer001 by numberGate.gate;
        satisfy reqVer002 by numberGate.gate;
        satisfy reqVer003 by numberGate.gate;
        satisfy reqVer004 by numberGate.gate;
        satisfy reqVer005 by numberGate.gate;
        satisfy reqVer006 by numberGate.gate;
        satisfy reqVer007 by numberGate.gate;
        satisfy reqStab001 by numberGate.stability;
        satisfy reqStab002 by numberGate.stability;
        satisfy reqStab003 by numberGate.lookup;
        satisfy reqEval001 by numberGate.harness;
        satisfy reqEval002 by numberGate.harness;
        satisfy reqEval003 by numberGate.harness;
        satisfy reqEval004 by numberGate.harness;
        satisfy nfrBud001 by numberGate.gate;

        // derivation: component requirements serve the system requirements (child from, parent to)
        dependency depGate001 from reqGate001 to reqVer001;
        dependency depGate002 from reqGate002 to reqVer001;
        dependency depGate003 from reqGate003 to reqVer002;
        dependency depGate004 from reqGate004 to reqVer003;
        dependency depGate005 from reqGate005 to nfrBud001;
        dependency depNum001 from reqNum001 to reqGate002;
        dependency depNum002 from reqNum002 to reqGate003;
        dependency depNum003 from reqNum003 to reqGate001;
        dependency depNum004 from reqNum004 to reqGate003;
        dependency depNum005 from reqNum005 to reqGate001;
        dependency depNum006 from reqNum006 to reqGate001;
        dependency depArg001 from reqArg001 to reqGate003;
        dependency depIf001 from if001 to reqGate001;
        dependency depIf002 from if002 to reqGate003;
        dependency depIf003 from if003 to reqEval001;
        dependency depIf004 from if004 to reqStab001;
        dependency depIf005 from if005 to reqEval003;
        dependency depIf006 from if006 to reqGate004;
        dependency depStab001 from reqStab001 to reqVer005;
        dependency depStab002 from reqStab002 to reqVer006;
        dependency depStab003 from reqStab003 to reqStab001;
        dependency depEval003 from reqEval003 to reqVer005;
    }

    // ---------------------------------------------------------------
    // Verification (tests and the eval suites)
    // ---------------------------------------------------------------
    package Verification {
        private import Requirements::*;
        private import Structure::*;
        verification def TcGate001 { subject s : VerificationGate; objective { verify reqGate001; } }
        verification def TcGate002 { subject s : VerificationGate; objective { verify reqGate002; } }
        verification def TcGate003 { subject s : VerificationGate; objective { verify reqGate003; } }
        verification def TcGate004 { subject s : VerificationGate; objective { verify reqGate004; } }
        verification def TcGate005 { subject s : VerificationGate; objective { verify reqGate005; } }
        verification def TcNum001 { subject s : NumberCheck; objective { verify reqNum001; } }
        verification def TcNum002 { subject s : NumberCheck; objective { verify reqNum002; } }
        verification def TcNum003 { subject s : NumberCheck; objective { verify reqNum003; } }
        verification def TcNum004 { subject s : NumberCheck; objective { verify reqNum004; } }
        verification def TcNum005 { subject s : NumberCheck; objective { verify reqNum005; } }
        verification def TcNum006 { subject s : NumberCheck; objective { verify reqNum006; } }
        verification def TcArg001 { subject s : ArgueStep; objective { verify reqArg001; } }
        verification def TcIf001 { subject s : NumberCheck; objective { verify if001; } }
        verification def TcIf002 { subject s : JudgeStep; objective { verify if002; } }
        verification def TcIf003 { subject s : VerificationGate; objective { verify if003; } }
        verification def TcIf004 { subject s : Harness; objective { verify if004; } }
        verification def TcIf005 { subject s : Harness; objective { verify if005; } }
        verification def TcIf006 { subject s : SingleVoiceStep; objective { verify if006; } }
        verification def TcStab001 { subject s : StabilityMetric; objective { verify reqStab001; } }
        verification def TcStab002 { subject s : StabilityMetric; objective { verify reqStab002; } }
        verification def TcStab003 { subject s : LookupPipeline; objective { verify reqStab003; } }
        verification def TcEval001 { subject s : Harness; objective { verify reqEval001; } }
        verification def TcEval002 { subject s : Harness; objective { verify reqEval002; } }
        verification def TcEval003 { subject s : Harness; objective { verify reqEval003; } }
        verification def TcEval004 { subject s : Harness; objective { verify reqEval004; } }
        verification def EvVerdictsVitaminc {
            doc /* Suite EV-verdicts_vitaminc on MP-light, 3 repeats; decided on the holdout in Verify (eval_decide.py). */
            subject s : VerificationGate;
            objective { verify reqVer001; verify reqVer003; verify reqVer005; }
        }
        verification def EvVerdictsWikidata {
            doc /* Suite EV-verdicts_wikidata on MP-light, 3 repeats; decided on the holdout in Verify. */
            subject s : VerificationGate;
            objective { verify reqVer002; verify reqVer004; verify reqVer006; }
        }
        verification def EvVerdictsInjection {
            doc /* Red-team suite EV-verdicts_injection, 10 cases, all repeats must resist. */
            subject s : VerificationGate;
            objective { verify reqVer007; }
        }
        verification def BmGate001 { subject s : VerificationGate; objective { verify nfrBud001; } }
    }
}
