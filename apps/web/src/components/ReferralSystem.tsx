import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Gift, Copy, Check, Share2, Users, DollarSign, Sparkles, X } from "lucide-react";
import { Button } from "./ui/Button";
import { cn } from "../lib/utils";
import { pushToast } from "../lib/toast";

interface ReferralModalProps {
  isOpen: boolean;
  onClose: () => void;
  userName?: string;
}

export function ReferralModal({ isOpen, onClose, userName }: ReferralModalProps) {
  const [copied, setCopied] = React.useState(false);
  const referralCode = "FRIEND50";
  const referralLink = `https://jobhuntin.com/login?ref=${referralCode}`;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(referralLink);
      setCopied(true);
      pushToast({
        title: "Link copied!",
        description: "Share it with your friends",
        tone: "success"
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      pushToast({
        title: "Failed to copy",
        description: "Please copy the link manually",
        tone: "error"
      });
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: "Get 50% off JobHuntin Pro",
          text: `${userName || "Someone"} thinks you'd love JobHuntin - AI-powered job search automation!`,
          url: referralLink
        });
      } catch (err) {
        // User cancelled
      }
    } else {
      handleCopy();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="relative bg-white dark:bg-slate-900 rounded-3xl shadow-2xl max-w-md w-full overflow-hidden"
          >
            {/* Header */}
            <div className="bg-gradient-to-br from-primary-600 to-primary-700 p-6 text-white">
              <button
                onClick={onClose}
                className="absolute top-4 right-4 p-2 text-white/80 hover:text-white hover:bg-white/10 rounded-full transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
              
              <div className="flex items-center gap-3 mb-3">
                <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center">
                  <Gift className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-xl font-black">Give 50%, Get 50%</h2>
                  <p className="text-white/80 text-sm">Share the love</p>
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 p-6 border-b border-slate-100 dark:border-slate-800">
              <div className="text-center">
                <Users className="w-5 h-5 mx-auto mb-1 text-slate-400" />
                <p className="text-2xl font-black text-slate-900 dark:text-slate-100">0</p>
                <p className="text-xs text-slate-500">Friends joined</p>
              </div>
              <div className="text-center">
                <DollarSign className="w-5 h-5 mx-auto mb-1 text-slate-400" />
                <p className="text-2xl font-black text-slate-900 dark:text-slate-100">$0</p>
                <p className="text-xs text-slate-500">You've earned</p>
              </div>
              <div className="text-center">
                <Sparkles className="w-5 h-5 mx-auto mb-1 text-slate-400" />
                <p className="text-2xl font-black text-slate-900 dark:text-slate-100">50%</p>
                <p className="text-xs text-slate-500">Off for friends</p>
              </div>
            </div>

            {/* Referral Link */}
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Your referral link
                </label>
                <div className="flex gap-2">
                  <div className="flex-1 px-4 py-3 bg-slate-50 dark:bg-slate-800 rounded-xl text-sm text-slate-600 dark:text-slate-400 truncate">
                    {referralLink}
                  </div>
                  <Button
                    onClick={handleCopy}
                    variant="outline"
                    className="px-4"
                  >
                    {copied ? (
                      <Check className="w-4 h-4 text-emerald-500" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>

              <Button
                onClick={handleShare}
                className="w-full h-12 rounded-xl"
              >
                <Share2 className="w-4 h-4 mr-2" />
                Share with friends
              </Button>

              <p className="text-xs text-center text-slate-500">
                Your friends get 50% off their first month. You get 50% off for each friend who subscribes.
              </p>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

// Referral button for dashboard
interface ReferralButtonProps {
  className?: string;
}

export function ReferralButton({ className }: ReferralButtonProps) {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className={cn(
          "flex items-center gap-2 px-4 py-2 rounded-xl",
          "bg-gradient-to-r from-primary-600 to-primary-500",
          "text-white font-semibold text-sm",
          "hover:from-primary-500 hover:to-primary-400",
          "transition-all shadow-lg shadow-primary-500/20",
          className
        )}
      >
        <Gift className="w-4 h-4" />
        Invite friends
      </button>

      <ReferralModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
      />
    </>
  );
}

export default ReferralModal;
