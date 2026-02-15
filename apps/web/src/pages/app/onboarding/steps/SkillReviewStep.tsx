import * as React from "react";
import { Star, Edit2, Trash2, Plus, Check, X, AlertCircle, Sparkles, ArrowLeft, ArrowRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "../../../../components/ui/Button";
import { Input } from "../../../../components/ui/Input";
import { LoadingSpinner } from "../../../../components/ui/LoadingSpinner";
import { RichSkill } from "../../../../types/onboarding";

interface SkillReviewStepProps {
    onNext: () => void;
    onPrev: () => void;
    richSkills: RichSkill[];
    setRichSkills: React.Dispatch<React.SetStateAction<RichSkill[]>>;
    isSaving: boolean;
}

function getConfidenceLevel(confidence: number): { label: string; color: string; bgColor: string } {
    if (confidence >= 0.8) {
        return { label: "HIGH", color: "text-emerald-600", bgColor: "bg-emerald-100" };
    } else if (confidence >= 0.5) {
        return { label: "MEDIUM", color: "text-amber-600", bgColor: "bg-amber-100" };
    } else {
        return { label: "LOW", color: "text-red-500", bgColor: "bg-red-100" };
    }
}

function ConfidenceBadge({ confidence }: { confidence: number }) {
    const { label, color, bgColor } = getConfidenceLevel(confidence);
    return (
        <span className={`px-1.5 md:px-2 py-0.5 text-[8px] md:text-[10px] font-black rounded-full ${bgColor} ${color}`}>
            {label}
        </span>
    );
}

interface SkillRowProps {
    skill: RichSkill;
    onEdit: () => void;
    onDelete: () => void;
}

function SkillRow({ skill, onEdit, onDelete }: SkillRowProps) {
    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="flex items-center gap-2 md:gap-4 p-2 md:p-3 rounded-xl bg-white border border-slate-100 hover:border-slate-200 transition-colors group"
        >
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                    <span className="font-bold text-slate-900 text-sm md:text-base truncate">{skill.skill}</span>
                    <ConfidenceBadge confidence={skill.confidence} />
                    {skill.verified && (
                        <span className="px-1.5 py-0.5 text-[8px] font-bold rounded-full bg-blue-100 text-blue-600">VERIFIED</span>
                    )}
                </div>
                <div className="flex flex-wrap gap-x-3 gap-y-1 text-[10px] md:text-xs text-slate-500">
                    {skill.years_actual && (
                        <span className="flex items-center gap-1">
                            <Star className="w-3 h-3 text-slate-400" />
                            {skill.years_actual} yrs
                        </span>
                    )}
                    {skill.project_count > 0 && (
                        <span>{skill.project_count} projects</span>
                    )}
                    {skill.context && (
                        <span className="text-slate-400 truncate max-w-[200px]">{skill.context}</span>
                    )}
                </div>
                {skill.related_to.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                        {skill.related_to.slice(0, 3).map((related) => (
                            <span key={related} className="px-1.5 py-0.5 text-[8px] md:text-[10px] bg-slate-100 text-slate-500 rounded">
                                {related}
                            </span>
                        ))}
                    </div>
                )}
            </div>
            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                    onClick={onEdit}
                    className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
                    aria-label="Edit skill"
                >
                    <Edit2 className="w-3.5 h-3.5 md:w-4 md:h-4" />
                </button>
                <button
                    onClick={onDelete}
                    className="p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500 transition-colors"
                    aria-label="Delete skill"
                >
                    <Trash2 className="w-3.5 h-3.5 md:w-4 md:h-4" />
                </button>
            </div>
        </motion.div>
    );
}

interface AddSkillFormProps {
    onAdd: (skill: RichSkill) => void;
    onCancel: () => void;
}

function AddSkillForm({ onAdd, onCancel }: AddSkillFormProps) {
    const [skillName, setSkillName] = React.useState("");
    const [years, setYears] = React.useState("");
    const [context, setContext] = React.useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!skillName.trim()) return;

        const newSkill: RichSkill = {
            skill: skillName.trim(),
            confidence: 0.5,
            years_actual: years ? parseFloat(years) : null,
            context: context.trim(),
            last_used: null,
            verified: false,
            related_to: [],
            source: "manual",
            project_count: 0,
        };

        onAdd(newSkill);
        setSkillName("");
        setYears("");
        setContext("");
    };

    return (
        <motion.form
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            onSubmit={handleSubmit}
            className="p-3 md:p-4 rounded-xl bg-emerald-50 border border-emerald-200 space-y-3"
        >
            <div className="flex items-center gap-2">
                <Plus className="w-4 h-4 text-emerald-600" />
                <span className="font-bold text-emerald-800 text-sm">Add a Skill</span>
            </div>
            <div className="grid gap-2 md:grid-cols-3">
                <Input
                    type="text"
                    placeholder="Skill name"
                    value={skillName}
                    onChange={(e) => setSkillName(e.target.value)}
                    className="bg-white text-sm"
                />
                <Input
                    type="number"
                    placeholder="Years"
                    value={years}
                    onChange={(e) => setYears(e.target.value)}
                    className="bg-white text-sm"
                    min="0"
                    max="50"
                    step="0.5"
                />
                <Input
                    type="text"
                    placeholder="Context (optional)"
                    value={context}
                    onChange={(e) => setContext(e.target.value)}
                    className="bg-white text-sm"
                />
            </div>
            <div className="flex justify-end gap-2">
                <Button type="button" variant="ghost" onClick={onCancel} className="h-8 text-xs">
                    <X className="w-3 h-3 mr-1" />
                    Cancel
                </Button>
                <Button type="submit" disabled={!skillName.trim()} className="h-8 text-xs bg-emerald-600 hover:bg-emerald-500">
                    <Check className="w-3 h-3 mr-1" />
                    Add Skill
                </Button>
            </div>
        </motion.form>
    );
}

export function SkillReviewStep({
    onNext,
    onPrev,
    richSkills,
    setRichSkills,
    isSaving,
}: SkillReviewStepProps) {
    const [isAddingSkill, setIsAddingSkill] = React.useState(false);
    const [editingIndex, setEditingIndex] = React.useState<number | null>(null);

    const highSkills = richSkills.filter(s => s.confidence >= 0.8);
    const mediumSkills = richSkills.filter(s => s.confidence >= 0.5 && s.confidence < 0.8);
    const lowSkills = richSkills.filter(s => s.confidence < 0.5);

    const handleAddSkill = (skill: RichSkill) => {
        setRichSkills(prev => [...prev, skill]);
        setIsAddingSkill(false);
    };

    const handleDeleteSkill = (index: number) => {
        setRichSkills(prev => prev.filter((_, i) => i !== index));
    };

    const handleUpdateSkill = (index: number, updates: Partial<RichSkill>) => {
        setRichSkills(prev => prev.map((s, i) => i === index ? { ...s, ...updates } : s));
        setEditingIndex(null);
    };

    return (
        <div className="flex flex-col h-full overflow-hidden">
            <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 md:pr-2">
                <div className="mb-3 md:mb-6 flex items-center gap-2.5 md:gap-5 border-b border-slate-100 pb-2.5 md:pb-6">
                    <div className="flex h-8 w-10 md:h-12 md:w-16 shrink-0 items-center justify-center rounded-[0.75rem] md:rounded-[1.5rem] bg-emerald-50 border border-emerald-100 text-emerald-600 shadow-inner">
                        <Sparkles className="h-4 w-4 md:h-8 md:w-8" />
                    </div>
                    <div className="min-w-0">
                        <h2 className="font-display text-lg md:text-3xl font-black text-slate-900 tracking-tight truncate">Review Your Skills</h2>
                        <p className="text-[10px] md:text-sm text-slate-500 font-medium italic truncate">Verify the skills we detected from your resume.</p>
                    </div>
                </div>

                {richSkills.length === 0 ? (
                    <div className="text-center py-8 md:py-12">
                        <AlertCircle className="w-8 h-8 md:w-12 md:h-12 text-slate-300 mx-auto mb-3" />
                        <p className="text-slate-500 text-sm">No skills detected from your resume.</p>
                        <Button
                            onClick={() => setIsAddingSkill(true)}
                            className="mt-4 h-9 text-xs"
                        >
                            <Plus className="w-3 h-3 mr-1" />
                            Add Your First Skill
                        </Button>
                    </div>
                ) : (
                    <div className="space-y-4 md:space-y-6">
                        {highSkills.length > 0 && (
                            <div>
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-[10px] md:text-xs font-black text-emerald-600 uppercase tracking-wider">High Confidence</span>
                                    <span className="text-[10px] md:text-xs text-slate-400">({highSkills.length} skills)</span>
                                </div>
                                <div className="space-y-2">
                                    {highSkills.map((skill, idx) => {
                                        const globalIdx = richSkills.findIndex(s => s === skill);
                                        return (
                                            <SkillRow
                                                key={skill.skill}
                                                skill={skill}
                                                onEdit={() => setEditingIndex(globalIdx)}
                                                onDelete={() => handleDeleteSkill(globalIdx)}
                                            />
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {mediumSkills.length > 0 && (
                            <div>
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-[10px] md:text-xs font-black text-amber-600 uppercase tracking-wider">Medium Confidence</span>
                                    <span className="text-[10px] md:text-xs text-slate-400">({mediumSkills.length} skills)</span>
                                </div>
                                <div className="space-y-2">
                                    {mediumSkills.map((skill) => {
                                        const globalIdx = richSkills.findIndex(s => s === skill);
                                        return (
                                            <SkillRow
                                                key={skill.skill}
                                                skill={skill}
                                                onEdit={() => setEditingIndex(globalIdx)}
                                                onDelete={() => handleDeleteSkill(globalIdx)}
                                            />
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {lowSkills.length > 0 && (
                            <div>
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-[10px] md:text-xs font-black text-red-500 uppercase tracking-wider">Low Confidence</span>
                                    <span className="text-[10px] md:text-xs text-slate-400">({lowSkills.length} skills)</span>
                                    <span className="text-[10px] md:text-xs text-slate-400">- Consider verifying or removing</span>
                                </div>
                                <div className="space-y-2">
                                    {lowSkills.map((skill) => {
                                        const globalIdx = richSkills.findIndex(s => s === skill);
                                        return (
                                            <SkillRow
                                                key={skill.skill}
                                                skill={skill}
                                                onEdit={() => setEditingIndex(globalIdx)}
                                                onDelete={() => handleDeleteSkill(globalIdx)}
                                            />
                                        );
                                    })}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                <AnimatePresence>
                    {isAddingSkill && (
                        <AddSkillForm
                            onAdd={handleAddSkill}
                            onCancel={() => setIsAddingSkill(false)}
                        />
                    )}
                </AnimatePresence>

                {!isAddingSkill && (
                    <Button
                        variant="outline"
                        onClick={() => setIsAddingSkill(true)}
                        className="mt-4 h-9 md:h-10 text-xs md:text-sm w-full border-dashed border-slate-300 text-slate-500 hover:text-slate-700 hover:border-slate-400"
                    >
                        <Plus className="w-3 h-3 md:w-4 md:h-4 mr-1 md:mr-2" />
                        Add Missing Skill
                    </Button>
                )}

                <div className="mt-4 md:mt-6 p-2.5 md:p-4 rounded-xl bg-blue-50 border border-blue-100">
                    <div className="flex items-start gap-2">
                        <AlertCircle className="w-4 h-4 text-blue-600 mt-0.5 shrink-0" />
                        <div>
                            <p className="text-[10px] md:text-xs font-bold text-blue-800">Why does confidence matter?</p>
                            <p className="text-[10px] md:text-xs text-blue-700 mt-1">
                                Higher confidence skills are weighted more in job matching. You can edit or remove skills that don't reflect your expertise.
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="flex gap-3 md:gap-4 pt-2 md:pt-4 shrink-0 mt-auto sticky bottom-0 bg-gradient-to-t from-white via-white/95 to-transparent backdrop-blur">
                <Button variant="ghost" onClick={onPrev} className="h-9 md:h-12 rounded-[1.25rem] font-black text-slate-400 hover:text-slate-900 border-2 border-slate-100 hover:bg-slate-50 transition-all text-[10px] md:text-base px-3 md:px-4" aria-label="Go to previous step">
                    <ArrowLeft className="mr-1 md:mr-2 h-3.5 w-3.5 md:h-5 md:w-5" />
                    PREV
                </Button>
                <Button
                    onClick={onNext}
                    disabled={richSkills.length === 0 || isSaving}
                    className="flex-[2] h-9 md:h-12 rounded-[1.25rem] font-black bg-emerald-600 hover:bg-emerald-500 shadow-2xl shadow-emerald-500/30 text-xs md:text-lg disabled:opacity-50 disabled:cursor-not-allowed group"
                    aria-label="Confirm skills and continue"
                >
                    {isSaving ? <LoadingSpinner size="sm" /> : (
                        <>
                            CONFIRM SKILLS
                            <ArrowRight className="ml-1 md:ml-2 h-3.5 w-3.5 md:h-5 md:w-5 group-hover:translate-x-1 transition-transform" />
                        </>
                    )}
                </Button>
            </div>
        </div>
    );
}
