with open('src/lib/api.ts', 'r', encoding='utf-8') as f:
    code = f.read()

new_api = '''
export interface CycleTestQuestion {
  q_num: number;
  question_text: string;
  marks: number;
  q_type: string;
  answer_key: string | null;
  subject: string;
  cycle: string;
  source_file: string;
}

export interface CycleTestQuestionsResponse {
  subject: string;
  cycle: string;
  total_available: number;
  questions: CycleTestQuestion[];
}

export async function getCycleTestQuestions(
  subject: string,
  cycle?: string,
  limit: number = 50
): Promise<CycleTestQuestionsResponse> {
  const params = new URLSearchParams();
  if (cycle && cycle !== "ALL") params.set("cycle", cycle);
  params.set("limit", String(limit));
  try {
    return await fetchAPI(`/practice/cycle-tests/${encodeURIComponent(subject)}?${params.toString()}`);
  } catch (err) {
    return {
      subject,
      cycle: cycle || "ALL",
      total_available: 0,
      questions: []
    };
  }
}
'''

code += new_api

with open('src/lib/api.ts', 'w', encoding='utf-8') as f:
    f.write(code)

print("src/lib/api.ts updated successfully with getCycleTestQuestions!")
