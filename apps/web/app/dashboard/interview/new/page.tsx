import { FeatureFlag } from "@/hooks/use-feature-flag";
import { InterviewSetupHome } from "@/features/interview/components/InterviewSetupHome";

export default function NewInterviewPage() {
  return (
    <FeatureFlag name="interviews">
      <InterviewSetupHome />
    </FeatureFlag>
  );
}
