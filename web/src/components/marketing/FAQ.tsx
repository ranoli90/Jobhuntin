import * as React from "react";
import { ChevronDown, Shield, HelpCircle } from "lucide-react";
import { cn } from "../../lib/utils";

const FAQS = [
  {
    question: "Is this legit? Will I get banned from job sites?",
    answer: "Absolutely legit. We follow each platform's Terms of Service. We don't spam, we don't use bots that violate rate limits, and we never submit low-quality applications. We're essentially a very smart assistant that helps you apply faster—think of us like having a recruiter on your side.",
    icon: Shield,
  },
  {
    question: "How is this different from just applying myself?",
    answer: "Speed and quality. Most people take 20-30 minutes per application. We do it in under 2 minutes, and we customize every resume and cover letter using AI that understands what each employer is looking for. You couldn't humanly apply to 50 tailored jobs in a day. We can.",
    icon: HelpCircle,
  },
  {
    question: "What happens to my resume and data?",
    answer: "Your data is yours. We store it securely (encrypted at rest), never sell it to third parties, and you can delete everything anytime. We use your resume only to generate applications—you approve each one before it goes out.",
    icon: Shield,
  },
  {
    question: "Do employers know I used Skedaddle?",
    answer: "Nope. Every application comes from your email, with your name, using your LinkedIn profile. We just make you look incredibly organized and responsive. Employers see a polished, enthusiastic candidate—never a 'bot.'",
    icon: HelpCircle,
  },
  {
    question: "What if I want to customize an application?",
    answer: "You're always in control. Before any application goes out, you see a preview. You can edit the cover letter, tweak the resume bullets, or skip that job entirely. We're fast, but never pushy.",
    icon: HelpCircle,
  },
  {
    question: "How much does it cost?",
    answer: "Start free—10 applications on us. Then it's $19/month for unlimited personal use. Teams (recruiters, career coaches, bootcamps) pay $49/seat. No hidden fees, cancel anytime.",
    icon: HelpCircle,
  },
];

export function FAQ() {
  const [openIndex, setOpenIndex] = React.useState<number | null>(0);

  return (
    <section className="px-6 py-20">
      <div className="mx-auto max-w-3xl">
        <div className="mb-16 text-center">
          <p className="mb-2 text-sm uppercase tracking-[0.3em] text-brand-ink/50">Got questions?</p>
          <h2 className="font-display text-4xl text-brand-ink">Straight answers</h2>
        </div>

        <div className="space-y-4">
          {FAQS.map((faq, index) => {
            const Icon = faq.icon;
            const isOpen = openIndex === index;

            return (
              <div
                key={index}
                className={cn(
                  "rounded-3xl border border-white/70 bg-white transition-all",
                  isOpen && "shadow-lg"
                )}
              >
                <button
                  onClick={() => setOpenIndex(isOpen ? null : index)}
                  className="flex w-full items-center justify-between p-6 text-left"
                >
                  <div className="flex items-center gap-4">
                    <div className="rounded-xl bg-brand-shell p-2">
                      <Icon className="h-5 w-5 text-brand-ink" />
                    </div>
                    <span className="font-display text-lg text-brand-ink">{faq.question}</span>
                  </div>
                  <ChevronDown
                    className={cn(
                      "h-5 w-5 text-brand-ink/50 transition-transform",
                      isOpen && "rotate-180"
                    )}
                  />
                </button>

                {isOpen && (
                  <div className="px-6 pb-6">
                    <p className="pl-14 text-brand-ink/70 leading-relaxed">{faq.answer}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
