import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Mail, MessageSquare, Send, Clock, Shield, Users } from "lucide-react";
import { motion } from "framer-motion";
import { SEO } from "../components/marketing/SEO";
import { Button } from "../components/ui/Button";
import { t, getLocale } from "../lib/i18n";

export default function Contact() {
  const locale = getLocale();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    company: "",
    message: "",
    type: "general" as "general" | "support" | "sales" | "partnership",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Simulate form submission
    await new Promise((resolve) => setTimeout(resolve, 1500));

    setIsSubmitting(false);
    setSubmitted(true);
    setFormData({
      name: "",
      email: "",
      company: "",
      message: "",
      type: "general",
    });
  };

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >,
  ) => {
    setFormData((previous) => ({
      ...previous,
      [e.target.name]: e.target.value,
    }));
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-primary-500/20 selection:text-primary-700 flex items-center justify-center p-6">
        <SEO
          title="Message Sent | JobHuntin"
          description="Your message has been received. We'll get back to you within 24 hours."
          canonicalUrl="https://jobhuntin.com/contact"
          noindex
        />
        <div className="max-w-md w-full text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white dark:bg-slate-900 rounded-3xl p-8 shadow-xl border border-slate-100 dark:border-slate-700"
          >
            <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Send className="w-8 h-8 text-emerald-600" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-4">
              {t("contact.messageSent", locale)}
            </h1>
            <p className="text-slate-600 dark:text-slate-400 mb-8">
              {t("contact.messageSentDescription", locale)}
            </p>
            <Link to="/">
              <Button variant="secondary" className="w-full">
                {t("contact.backToHomepage", locale)}
              </Button>
            </Link>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 font-sans text-slate-900 dark:text-slate-100 selection:bg-primary-500/20 selection:text-primary-700">
      <SEO
        title="Contact JobHuntin | Get in Touch with Our Team"
        description="Have questions about JobHuntin's AI job search automation? Contact our team for support, sales inquiries, or partnership opportunities."
        ogTitle="Contact JobHuntin | Get in Touch"
        canonicalUrl="https://jobhuntin.com/contact"
        schema={{
          "@context": "https://schema.org",
          "@type": "ContactPage",
          name: "Contact JobHuntin",
          description:
            "Contact JobHuntin for support, sales, and partnership inquiries",
          url: "https://jobhuntin.com/contact",
        }}
      />

      <main className="max-w-7xl mx-auto px-6 py-28 sm:py-32">
        {/* Header */}
        <div className="text-center mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 bg-primary-50 text-primary-600 px-4 py-1 rounded-full text-sm font-bold mb-6 border border-primary-100"
          >
            <MessageSquare className="w-4 h-4" />
            {t("contact.getInTouch", locale)}
          </motion.div>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-sans font-black mb-6 leading-tight text-slate-900 dark:text-slate-100 text-balance">
            {t("contact.headingLine1", locale)} <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-blue-400">
              {t("contact.headingLine2", locale)}
            </span>
          </h1>
          <p className="text-lg sm:text-xl text-slate-500 dark:text-slate-400 max-w-2xl mx-auto font-medium text-balance">
            {t("contact.subtitle", locale)}
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-16 items-start">
          {/* Contact Form */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 shadow-xl border border-slate-100 dark:border-slate-700">
              <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6">
                {t("contact.sendMessage", locale)}
              </h2>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid sm:grid-cols-2 gap-6">
                  <div>
                    <label
                      htmlFor="name"
                      className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"
                    >
                      {t("contact.name", locale)} *
                    </label>
                    <input
                      type="text"
                      id="name"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      required
                      className="w-full px-4 py-3 border border-slate-200 dark:border-slate-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                      placeholder="John Doe"
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="email"
                      className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"
                    >
                      {t("contact.email", locale)} *
                    </label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      required
                      className="w-full px-4 py-3 border border-slate-200 dark:border-slate-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                      placeholder="john@example.com"
                    />
                  </div>
                </div>

                <div>
                  <label
                    htmlFor="company"
                    className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"
                  >
                    {t("contact.company", locale)}
                  </label>
                  <input
                    type="text"
                    id="company"
                    name="company"
                    value={formData.company}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border border-slate-200 dark:border-slate-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                    placeholder={t("contact.companyPlaceholder", locale)}
                  />
                </div>

                <div>
                  <label
                    htmlFor="type"
                    className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"
                  >
                    {t("contact.inquiryType", locale)}
                  </label>
                  <select
                    id="type"
                    name="type"
                    value={formData.type}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border border-slate-200 dark:border-slate-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                  >
                    <option value="general">
                      {t("contact.generalQuestion", locale)}
                    </option>
                    <option value="support">
                      {t("contact.technicalSupport", locale)}
                    </option>
                    <option value="sales">
                      {t("contact.salesInquiry", locale)}
                    </option>
                    <option value="partnership">
                      {t("contact.partnership", locale)}
                    </option>
                  </select>
                </div>

                <div>
                  <label
                    htmlFor="message"
                    className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"
                  >
                    {t("contact.message", locale)} *
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    value={formData.message}
                    onChange={handleChange}
                    required
                    rows={5}
                    className="w-full px-4 py-3 border border-slate-200 dark:border-slate-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all resize-none bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                    placeholder={t("contact.messagePlaceholder", locale)}
                  />
                </div>

                <Button
                  type="submit"
                  disabled={isSubmitting}
                  variant="primary"
                  size="lg"
                  className="w-full py-4 text-lg font-bold"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                      {t("contact.sending", locale)}
                    </>
                  ) : (
                    <>
                      {t("contact.sendMessageBtn", locale)}{" "}
                      <Send className="w-5 h-5 ml-2" />
                    </>
                  )}
                </Button>
              </form>
            </div>
          </motion.div>

          {/* Contact Information */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="space-y-8"
          >
            <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 shadow-xl border border-slate-100 dark:border-slate-700">
              <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6">
                {t("contact.otherWays", locale)}
              </h2>

              <div className="space-y-6">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-primary-50 rounded-xl flex items-center justify-center flex-shrink-0">
                    <Mail className="w-6 h-6 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-1">
                      {t("contact.emailLabel", locale)}
                    </h3>
                    <p className="text-slate-600 dark:text-slate-400">
                      support@jobhuntin.com
                    </p>
                    <p className="text-sm text-slate-400">
                      {t("contact.respondWithin24", locale)}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
                    <Users className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-1">
                      {t("contact.salesTeam", locale)}
                    </h3>
                    <p className="text-slate-600 dark:text-slate-400">
                      sales@jobhuntin.com
                    </p>
                    <p className="text-sm text-slate-400">
                      {t("contact.salesHint", locale)}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-emerald-50 rounded-xl flex items-center justify-center flex-shrink-0">
                    <Shield className="w-6 h-6 text-emerald-600" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-1">
                      {t("contact.securityPrivacy", locale)}
                    </h3>
                    <p className="text-slate-600 dark:text-slate-400">
                      privacy@jobhuntin.com
                    </p>
                    <p className="text-sm text-slate-400">
                      {t("contact.privacyHint", locale)}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-primary-500 to-primary-600 rounded-3xl p-8 text-white shadow-xl">
              <h3 className="text-2xl font-bold mb-4">
                {t("contact.needImmediateHelp", locale)}
              </h3>
              <p className="text-white/90 mb-6">
                {t("contact.faqHint", locale)}
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  to="/guides"
                  className="bg-white text-primary-600 px-6 py-3 rounded-xl font-bold hover:bg-slate-50 transition-colors text-center"
                >
                  {t("contact.browseGuides", locale)}
                </Link>
                <Link
                  to="/pricing"
                  className="bg-white/10 hover:bg-white/20 px-6 py-3 rounded-xl font-bold transition-colors border border-white/20 text-center"
                >
                  {t("contact.viewPricing", locale)}
                </Link>
              </div>
            </div>

            <div className="bg-slate-100 dark:bg-slate-800 rounded-3xl p-8 text-center">
              <Clock className="w-8 h-8 text-slate-400 mx-auto mb-4" />
              <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2">
                {t("contact.responseTime", locale)}
              </h3>
              <p className="text-slate-600 dark:text-slate-400 text-sm">
                {t("contact.responseTimeDesc", locale)}
              </p>
            </div>
          </motion.div>
        </div>
      </main>
    </div>
  );
}
