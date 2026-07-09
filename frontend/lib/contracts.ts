// Friendly, hand-named types for the app to import.
//
// `lib/types.ts` is GENERATED from the backend OpenAPI schema by `make gen-types`
// (do not hand-edit it). This module is the stable, hand-maintained seam over it:
// it re-exports the generated component schemas under the names the rest of the
// codebase uses, and narrows the few fields the schema can only express as plain
// strings / free-form objects (status, current_step, kyc) to their locked SPEC
// shapes. Import app types from here, never from `./types`.

import type { components } from './types'

type Schemas = components['schemas']

// The backend serializes these as plain strings; narrow to the locked SPEC values.
export type AnalysisStatus = 'queued' | 'running' | 'done' | 'failed'

export type PipelineStep =
  | 'discovery'
  | 'kyc'
  | 'prompts'
  | 'execute'
  | 'footprint'
  | 'scoring'

// KYC is stored/serialized as a free-form JSON object; this is its locked shape.
export interface KYC {
  company: string
  description: string
  industry: string
  aliases: string[]
  products: string[]
  services: string[]
  keywords: string[]
  locations: string[]
  competitors: string[]
}

export type Prompt = Schemas['PromptOut']

export type AnalysisResponse = Schemas['ResponseOut']

export type CreateAnalysisResponse = Schemas['CreateAnalysisResponse']

export type AnalysisResult = Omit<Schemas['ResultOut'], 'kyc'> & {
  kyc: KYC | null
}

export type Analysis = Omit<
  Schemas['AnalysisOut'],
  'status' | 'current_step' | 'result'
> & {
  status: AnalysisStatus
  current_step: PipelineStep | null
  result: AnalysisResult
}
