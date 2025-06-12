AnkiVoice is a smart, voice-driven application that transforms the traditional flashcard experience by combining Generative AI with speech recognition and synthesis — all running on the edge.

Spaced repetition is a powerful learning technique where information is reviewed at increasing intervals to improve long-term memory retention. Tools like Anki are popular among students, professionals, and language learners — but the interaction is often passive and text-heavy. AnkiVoice aims to make active recall feel natural, fast, and more engaging.

The core idea is simple: you feed in your study material (notes, textbook content, lecture transcripts), and the system automatically generates questions using a local language model. These questions are converted into audio prompts. During revision, the user interacts by speaking their answers. The app uses on-device speech recognition to transcribe responses and a local language model to evaluate them. The response quality is used to decide whether to reschedule the card sooner or later, in true spaced repetition fashion. All answers are read aloud with natural-sounding TTS, making the entire experience hands-free.

This setup turns revision into a conversation. You could be walking, cooking, or commuting and still get a solid review session in — just by listening and responding.

What makes this ideal for edge AI: it needs to work in real time, without lag, and ideally without requiring internet access. Speech recognition, TTS, and LLM-based evaluation are all computationally intensive but feasible on modern edge hardware.

AnkiVoice turns revision from a static, solo activity into an interactive dialogue — reducing screen time and helping ideas stick better. It's flashcards, reimagined for voice and AI.

The above project description can be decomposed into 2 Problems.

Problem - I : Take a Statement, Fact, Theorem, etc... and convert it into a series of questions that a user can choose from, where each question has the same answer but asks the question from a different perspective.

Example: "Statement: Gradients point to the direction of the steepest ascent"

QA: 
1. In which direction do the Gradients point? Steepest Ascent
2. What's the mathematical term for the vectors that point to the direction of the steepest ascent? GRADIENTS.

Of course, based on the chosen LLM, we can also infuse world knowledge and refine the generated question-answers further.

Example: In Deep Learning, if we're trying to minimise loss, do we subtract or add the gradient vectors and why Subtract cuz they point to the direction of steepest ascent.


--------------------------------------------------

Problem-II: While reviewing cards, they way I and honestly everyone do is by 
1. Look at the Question 
   2.  Think of an answer in mind
3. Look at the actual answer
4. Decide how easy or hard it felt, based on which the system will decide when to ask this question again.

With the use of {ASR, LLM, TTS} or {ALLM, TTS}, we can make this mundane affair into something more dynamic. The user can do long walks, do pushups, sit on the sofa, get massage and still do the cards, and do them in a more engaging way.

So, TTS can take (1), ASR can take (2), LLM will take (3,4).

Here, too, to steal the hearts of the people, we can offer multiple modes:

1. Default Mode: TTS will speak, ASR will transcribe and directly send it to LLM.
2. Controlled Mode: ASR will Transcribe, but the user will send the transcription to LLM after reviewing it. The TTS will read out the Qs and Feedback.
3. No TTS mode: user will only use ASR+LLM but read off the Qs from screen
4. LLM-neednt-make-decision-mode: The final decision about how correct the answer was and how soon should it be asked again will be offloaded to the user in this mode.

There are 3-4 modes more like these.

Not only are these useful from a user point-of-view (I use Anki almost daily from the last 3 years), but will also give us an opportunity to showcase our depth, NPU Utilization, etc... which are a criterion in the scoring, and importantly allow for good demo & showmanship.