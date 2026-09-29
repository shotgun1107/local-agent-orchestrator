"""Bounded data-only function-call wire format; no pickle, eval or code objects."""
from __future__ import annotations

from datetime import datetime
import json
import math
from pathlib import Path
from types import SimpleNamespace

from pydantic import BaseModel

LIMIT = 1_048_576
MODELS = frozenset('''EmbeddedJsonEvidence JsonRpcFrameEvidence JsonRpcMethodLedger Win32CallObservation
WindowsProcessIdentityObservation FileReadObservation FileMutationObservation ProbeProcessObservation
P01ReadResult P02ReadResult P03ReadResult EnumerationTargetObservation P04EnumerationResult LinkAttemptObservation
P05LinkResult P06ChildResult P07InputScanResult P08StateResult RuntimeIdentity ConfigurationExpectation RootIdentity
SentinelSpec ProbeFixtureSpec ProbeCommandSpec RuntimeBoundaryProbeManifest SdkProfileProvenanceObservation
PolicySourceIdentity EffectivePolicyProjection EffectivePolicyEvidence WorkspaceAclTransitionObservation
WindowsSandboxProvenanceObservation RuntimeBoundaryProbeResult RuntimeBoundaryBundleSeal'''.split())
OPERATIONS = frozenset('''sdk_profile_evidence_from_transcript verify_sdk_profile_provenance collect_sdk_profile_provenance
build_runtime_boundary_manifest verify_probe_command_contract ConfigurationExpectation.model_validate
RuntimeBoundaryProbeManifest.model_validate derive_windows_sandbox_kind verify_workspace_acl_transition
_parse_workspace_acl_ace _assert_controller_only_directory_security probe._link_attempt recompute_probe_pass
project_effective_policy effective_policy_evidence_from_projection verify_effective_policy
effective_policy_failure_reason_codes build_windows_sandbox_provenance result_with_recomputed_verdict
write_runtime_boundary_bundle verify_runtime_boundary_bundle _toml_basic_string'''.split())
CALLBACKS = ('start','initialize','account_read','_request_raw','_request_raw','wait_for_notification','close','transcript')


class WireError(ValueError): pass


def bounded(value, depth=0):
    if depth > 48: raise WireError('DEPTH')
    if type(value) is dict:
        if len(value)>256 or any(type(k) is not str or len(k)>512 for k in value): raise WireError('DICT')
        for item in value.values(): bounded(item,depth+1)
    elif type(value) is list:
        if len(value)>4096: raise WireError('LIST')
        for item in value: bounded(item,depth+1)
    elif type(value) is float:
        if not math.isfinite(value): raise WireError('NUMBER')
    elif type(value) not in (str,int,bool,type(None)): raise WireError('TYPE')


def pack(value):
    bounded(value)
    raw=(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()
    if len(raw)>LIMIT: raise WireError('SIZE')
    return raw


def parse(raw):
    if len(raw)>LIMIT: raise WireError('SIZE')
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise WireError('DUPLICATE')
            result[key]=value
        return result
    def invalid(_): raise WireError('NONFINITE')
    try: value=json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid)
    except (ValueError,UnicodeError,RecursionError) as error: raise WireError('JSON') from error
    bounded(value)
    return value


def encode(value, depth=0):
    if depth>40: raise WireError('DEPTH')
    descend=lambda v:encode(v,depth+1)
    if isinstance(value,BaseModel):
        name=type(value).__name__
        if name not in MODELS: raise WireError('MODEL')
        return {'t':'model','name':name,'fields':{k:descend(getattr(value,k)) for k in type(value).model_fields}}
    if isinstance(value,Path): return {'t':'path','value':str(value)}
    if isinstance(value,datetime): return {'t':'datetime','value':value.isoformat()}
    if isinstance(value,SimpleNamespace): return {'t':'namespace','fields':{k:descend(v) for k,v in vars(value).items()}}
    if type(value) is dict:
        if any(type(k) is not str for k in value): raise WireError('KEY')
        return {'t':'dict','fields':{k:descend(v) for k,v in value.items()}}
    if type(value) in (list,tuple): return {'t':'tuple' if type(value) is tuple else 'list','items':[descend(v) for v in value]}
    if isinstance(value,str): return str(value)
    if type(value) in (int,float,bool,type(None)):
        bounded(value)
        return value
    raise WireError('VALUE_TYPE')


def decode(value, registry, depth=0):
    if depth>40: raise WireError('DEPTH')
    descend=lambda v:decode(v,registry,depth+1)
    if type(value) in (str,int,float,bool,type(None)):
        bounded(value)
        return value
    if type(value) is not dict: raise WireError('TAGGED_VALUE')
    tag=value.get('t')
    if tag in ('path','datetime') and set(value)=={'t','value'} and type(value['value']) is str:
        return Path(value['value']) if tag=='path' else datetime.fromisoformat(value['value'])
    if tag in ('list','tuple') and set(value)=={'t','items'} and type(value['items']) is list:
        rows=[descend(v) for v in value['items']]
        return tuple(rows) if tag=='tuple' else rows
    if tag in ('dict','namespace','model'):
        keys={'t','fields','name'} if tag=='model' else {'t','fields'}
        if set(value)!=keys or type(value['fields']) is not dict: raise WireError('FIELDS')
        fields={k:descend(v) for k,v in value['fields'].items()}
        if tag=='dict': return fields
        if any(not k.isidentifier() or k.startswith('_') for k in fields): raise WireError('FIELD_NAME')
        if tag=='namespace': return SimpleNamespace(**fields)
        name=value['name']
        if type(name) is not str: raise WireError('MODEL_NAME')
        if name not in MODELS or name not in registry or set(fields)!=set(registry[name].model_fields): raise WireError('MODEL_FIELDS')
        # Deliberately preserve malformed model_copy inputs: the TARGET verifier
        # must reject them, not the wire decoder's model validation.
        return registry[name].model_construct(**fields)
    raise WireError('TAG')
