import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
);

const MOCK_USER_ID = '7c434704-b345-41a6-952b-10778ce8e24e';

const MOCK_TURNS = [
  {
    stage: 'INTRO',
    question: 'Tell me about yourself and your experience with software engineering.',
    answer:
      'I am a full-stack engineer with 5 years of experience building scalable web applications. I started at a startup where I owned the entire frontend, then moved to a mid-size company where I led the migration from a monolith to microservices. My technical stack includes React, Node.js, Python, and PostgreSQL. I am particularly strong in system design and API architecture.',
  },
  {
    stage: 'TECHNICAL',
    question: 'Walk me through how you would design a real-time chat application that supports millions of concurrent users.',
    answer:
      'I would start with WebSockets for bidirectional communication, using a gateway like AWS API Gateway WebSocket API. For message persistence, I would use Cassandra for its high write throughput. Redis would handle presence detection and typing indicators. The architecture would be horizontally scalable behind a load balancer, with each WebSocket server handling up to 10K connections. Messages would be acknowledged with a FIFO queue to guarantee ordering within a partition.',
  },
  {
    stage: 'BEHAVIORAL',
    question: 'Tell me about a time you had a disagreement with a team member. How did you handle it?',
    answer:
      'In my previous role, I disagreed with a senior engineer about the database choice for a new feature. He wanted to use MongoDB, but I believed PostgreSQL with JSONB columns was more appropriate given our strong relational data model. I scheduled a meeting where I prepared a comparison document outlining trade-offs — consistency guarantees, operational overhead, and team familiarity. After presenting the data, we agreed to run a small POC with PostgreSQL. The POC confirmed my recommendation. We shipped on time and the team adopted the approach for future features.',
  },
  {
    stage: 'WRAP_UP',
    question: 'Thank you for your time today. Do you have any questions for us?',
    answer:
      'Thank you for the opportunity. I am excited about the role and the team. I do not have additional questions at this time. I look forward to the next steps.',
  },
];

export async function GET() {
  try {
    const sessionId = crypto.randomUUID();

    const { error: sessionError } = await supabase
      .from('interview_sessions')
      .insert({
        id: sessionId,
        user_id: MOCK_USER_ID,
        target_role: 'Senior Full-Stack Engineer',
        difficulty: 'Senior',
        current_stage: 'WRAP_UP',
        is_completed: true,
        overall_assessment:
          'Strong candidate with solid system design knowledge and clear communication. Demonstrates good technical depth in backend architecture and thoughtful decision-making. Behavioral answers show structured thinking using STAR framework effectively. Recommend moving to final round.',
      });

    if (sessionError) {
      return new Response(
        JSON.stringify({ error: 'Failed to create session', detail: sessionError.message }),
        { status: 500, headers: { 'content-type': 'application/json' } },
      );
    }

    const insertedTurns: { id: string; seq: number }[] = [];

    for (let i = 0; i < MOCK_TURNS.length; i++) {
      const turnId = crypto.randomUUID();
      const turn = MOCK_TURNS[i];
      const seq = i + 1;

      const { error: turnError } = await supabase.from('interview_turns').insert({
        id: turnId,
        session_id: sessionId,
        sequence_number: seq,
        interviewer_question: turn.question,
        candidate_response: turn.answer,
      });

      if (turnError) {
        return new Response(
          JSON.stringify({ error: 'Failed to insert turn', detail: turnError.message }),
          { status: 500, headers: { 'content-type': 'application/json' } },
        );
      }

      insertedTurns.push({ id: turnId, seq });
    }

    const evaluations = [
      {
        turn_id: insertedTurns[0].id,
        technical_score: 7,
        communication_score: 8,
        star_framework_check: false,
        conciseness_score: 4,
        confidence_score: 4,
        code_quality_score: 4,
        constructive_critique:
          'Good overview of experience but lacked specific metrics. Mentioning team size, project impact, or quantifiable outcomes would strengthen the answer.',
        filler_words_detected: { um: 2, like: 1 },
      },
      {
        turn_id: insertedTurns[1].id,
        technical_score: 9,
        communication_score: 8,
        star_framework_check: false,
        conciseness_score: 5,
        confidence_score: 5,
        code_quality_score: 5,
        constructive_critique:
          'Excellent technical depth covering WebSocket architecture, database choice, and scaling strategy. The FIFO queue detail shows strong distributed systems knowledge.',
        filler_words_detected: {},
      },
      {
        turn_id: insertedTurns[2].id,
        technical_score: 6,
        communication_score: 9,
        star_framework_check: true,
        conciseness_score: 4,
        confidence_score: 4,
        code_quality_score: 5,
        constructive_critique:
          'Strong STAR answer with clear Situation, Task, Action, Result. The POC detail was excellent. Could have mentioned how the relationship was maintained post-resolution.',
        filler_words_detected: { actually: 1, basically: 1 },
      },
      {
        turn_id: insertedTurns[3].id,
        technical_score: 5,
        communication_score: 7,
        star_framework_check: false,
        conciseness_score: 5,
        confidence_score: 3,
        code_quality_score: 3,
        constructive_critique:
          'Brief and polite closing. Missing an opportunity — asking thoughtful questions about team culture or technical challenges would leave a stronger impression.',
        filler_words_detected: { thank: 2 },
      },
    ];

    for (const evalData of evaluations) {
      const { error: evalError } = await supabase
        .from('turn_evaluations')
        .upsert(evalData, { onConflict: 'turn_id' });

      if (evalError) {
        return new Response(
          JSON.stringify({ error: 'Failed to insert evaluation', detail: evalError.message }),
          { status: 500, headers: { 'content-type': 'application/json' } },
        );
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        sessionId,
        url: `/interview/${sessionId}/report`,
        turns: insertedTurns.length,
      }),
      { status: 200, headers: { 'content-type': 'application/json' } },
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return new Response(
      JSON.stringify({ error: message }),
      { status: 500, headers: { 'content-type': 'application/json' } },
    );
  }
}
