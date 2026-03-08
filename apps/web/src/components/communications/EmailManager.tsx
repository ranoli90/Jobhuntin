import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Mail, 
  Send, 
  Clock, 
  CheckCircle, 
  AlertTriangle, 
  Settings, 
  RefreshCw,
  Eye,
  EyeOff,
  Filter,
  Search,
  Download,
  Trash2
} from 'lucide-react';

interface EmailCommunication {
  id: string;
  subject: string;
  to_email: string;
  category: string;
  status: string;
  sent_at: string | null;
  error_message: string | null;
  created_at: string;
}

interface EmailPreferences {
  user_id: string;
  tenant_id: string;
  email_enabled: boolean;
  categories: Record<string, boolean>;
  frequency_limits: Record<string, number>;
  quiet_hours_enabled: boolean;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
  updated_at: string;
}

interface EmailTemplate {
  id: string;
  name: string;
  subject_template: string;
  body_template: string;
  variables: string[];
  category: string;
}

const EmailManager: React.FC = () => {
  const [emails, setEmails] = useState<EmailCommunication[]>([]);
  const [preferences, setPreferences] = useState<EmailPreferences | null>(null);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [showCompose, setShowCompose] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Compose form state
  const [composeForm, setComposeForm] = useState({
    to_email: '',
    subject: '',
    body: '',
    category: 'general',
    template_id: '',
    variables: {} as Record<string, string>,
  });

  // Preferences form state
  const [preferencesForm, setPreferencesForm] = useState({
    email_enabled: true,
    categories: {} as Record<string, boolean>,
    frequency_limits: {} as Record<string, number>,
    quiet_hours_enabled: false,
    quiet_hours_start: '',
    quiet_hours_end: '',
  });

  useEffect(() => {
    fetchEmails();
    fetchPreferences();
    fetchTemplates();
    
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchEmails();
      }, 30000);
      
      return () => clearInterval(interval);
    }
  }, [autoRefresh, selectedCategory]);

  const fetchEmails = async () => {
    try {
      const response = await fetch('/api/communications/email/history', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch emails');
      const data = await response.json();
      setEmails(data.emails || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch emails');
    } finally {
      setLoading(false);
    }
  };

  const fetchPreferences = async () => {
    try {
      const response = await fetch('/api/communications/email/preferences', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch preferences');
      const data = await response.json();
      setPreferences(data);
      setPreferencesForm({
        email_enabled: data.email_enabled,
        categories: data.categories,
        frequency_limits: data.frequency_limits,
        quiet_hours_enabled: data.quiet_hours_enabled,
        quiet_hours_start: data.quiet_hours_start || '',
        quiet_hours_end: data.quiet_hours_end || '',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch preferences');
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await fetch('/api/communications/email/templates', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch templates');
      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch templates');
    }
  };

  const handleSendEmail = async () => {
    try {
      const response = await fetch('/api/communications/email/send', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(composeForm),
      });

      if (!response.ok) throw new Error('Failed to send email');
      
      await fetchEmails();
      setShowCompose(false);
      setComposeForm({
        to_email: '',
        subject: '',
        body: '',
        category: 'general',
        template_id: '',
        variables: {},
      });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send email');
    }
  };

  const handleUpdatePreferences = async () => {
    try {
      const response = await fetch('/api/communications/email/preferences', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(preferencesForm),
      });

      if (!response.ok) throw new Error('Failed to update preferences');
      
      await fetchPreferences();
      setShowPreferences(false);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update preferences');
    }
  };

  const handleTemplateSelect = (templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (template) {
      setComposeForm({
        ...composeForm,
        template_id: templateId,
        subject: template.subject_template,
        body: template.body_template,
        category: template.category,
      });
    }
  };

  const getStatusColor = (status: string) => {
    const colors = {
      sent: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      failed: 'bg-red-100 text-red-800',
      bounced: 'bg-gray-100 text-gray-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (status: string) => {
    const icons = {
      sent: <CheckCircle className="h-4 w-4" />,
      pending: <Clock className="h-4 w-4" />,
      failed: <AlertTriangle className="h-4 w-4" />,
      bounced: <AlertTriangle className="h-4 w-4" />,
    };
    return icons[status] || <Clock className="h-4 w-4" />;
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);
    
    if (diffSeconds < 60) return 'Just now';
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)} minutes ago`;
    if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)} hours ago`;
    return `${Math.floor(diffSeconds / 86400)} days ago`;
  };

  const filteredEmails = selectedCategory === 'all' 
    ? emails 
    : emails.filter(email => email.category === selectedCategory);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Email Manager</h1>
          <p className="text-gray-600">Manage email communications and preferences</p>
        </div>
        <div className="flex space-x-2">
          <Button onClick={() => setShowCompose(true)}>
            <Mail className="h-4 w-4 mr-2" />
            Compose
          </Button>
          <Button variant="outline" onClick={() => setShowPreferences(true)}>
            <Settings className="h-4 w-4 mr-2" />
            Preferences
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            {autoRefresh ? 'Auto-refresh' : 'Manual refresh'}
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Email Compose Modal */}
      {showCompose && (
        <Card className="p-6">
          <CardHeader>
            <CardTitle>Compose Email</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="to-email">To Email</Label>
                <Input
                  id="to-email"
                  type="email"
                  placeholder="recipient@example.com"
                  value={composeForm.to_email}
                  onChange={(e) => setComposeForm({ ...composeForm, to_email: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="template">Template (Optional)</Label>
                <Select value={composeForm.template_id} onValueChange={handleTemplateSelect}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a template" />
                  </SelectTrigger>
                  <SelectContent>
                    {templates.map((template) => (
                      <SelectItem key={template.id} value={template.id}>
                        {template.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="subject">Subject</Label>
                <Input
                  id="subject"
                  placeholder="Email subject"
                  value={composeForm.subject}
                  onChange={(e) => setComposeForm({ ...composeForm, subject: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="body">Body</Label>
                <Textarea
                  id="body"
                  placeholder="Email body (HTML supported)"
                  rows={8}
                  value={composeForm.body}
                  onChange={(e) => setComposeForm({ ...composeForm, body: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="category">Category</Label>
                <Select value={composeForm.category} onValueChange={(value) => setComposeForm({ ...composeForm, category: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="general">General</SelectItem>
                    <SelectItem value="application_status">Application Status</SelectItem>
                    <SelectItem value="job_matches">Job Matches</SelectItem>
                    <SelectItem value="security">Security</SelectItem>
                    <SelectItem value="marketing">Marketing</SelectItem>
                    <SelectItem value="usage_limits">Usage Limits</SelectItem>
                    <SelectItem value="reminders">Reminders</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex space-x-2">
                <Button onClick={handleSendEmail} disabled={!composeForm.to_email || !composeForm.subject || !composeForm.body}>
                  <Send className="h-4 w-4 mr-2" />
                  Send Email
                </Button>
                <Button variant="outline" onClick={() => setShowCompose(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Email Preferences Modal */}
      {showPreferences && preferences && (
        <Card className="p-6">
          <CardHeader>
            <CardTitle>Email Preferences</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="flex items-center space-x-2">
                <Switch
                  id="email-enabled"
                  checked={preferencesForm.email_enabled}
                  onCheckedChange={(checked) => setPreferencesForm({ ...preferencesForm, email_enabled: checked })}
                />
                <Label htmlFor="email-enabled">Enable Email Communications</Label>
              </div>

              <div className="space-y-4">
                <h4 className="font-medium">Category Preferences</h4>
                <div className="space-y-2">
                  {Object.entries(preferencesForm.categories).map(([category, enabled]) => (
                    <div key={category} className="flex items-center space-x-2">
                      <Switch
                        id={`category-${category}`}
                        checked={enabled}
                        onCheckedChange={(checked) => {
                          setPreferencesForm({
                            ...preferencesForm,
                            categories: {
                              ...preferencesForm.categories,
                              [category]: checked,
                            },
                          });
                        }}
                      />
                      <Label htmlFor={`category-${category}`} className="capitalize">
                        {category.replace('_', ' ')}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-medium">Quiet Hours</h4>
                <div className="flex items-center space-x-2">
                  <Switch
                    id="quiet-hours-enabled"
                    checked={preferencesForm.quiet_hours_enabled}
                    onCheckedChange={(checked) => setPreferencesForm({ ...preferencesForm, quiet_hours_enabled: checked })}
                  />
                  <Label htmlFor="quiet-hours-enabled">Enable Quiet Hours</Label>
                </div>
                
                {preferencesForm.quiet_hours_enabled && (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="quiet-hours-start">Start Time</Label>
                      <Input
                        id="quiet-hours-start"
                        type="time"
                        value={preferencesForm.quiet_hours_start}
                        onChange={(e) => setPreferencesForm({ ...preferencesForm, quiet_hours_start: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="quiet-hours-end">End Time</Label>
                      <Input
                        id="quiet-hours-end"
                        type="time"
                        value={preferencesForm.quiet_hours_end}
                        onChange={(e) => setPreferencesForm({ ...preferencesForm, quiet_hours_end: e.target.value })}
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="flex space-x-2">
                <Button onClick={handleUpdatePreferences}>
                  <Settings className="h-4 w-4 mr-2" />
                  Update Preferences
                </Button>
                <Button variant="outline" onClick={() => setShowPreferences(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Category Filter */}
      <Card>
        <CardHeader>
          <CardTitle>Email History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2 mb-4">
            <Button
              variant={selectedCategory === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCategory('all')}
            >
              All Categories
            </Button>
            {['application_status', 'job_matches', 'security', 'marketing', 'usage_limits', 'reminders'].map((category) => (
              <Button
                key={category}
                variant={selectedCategory === category ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedCategory(category)}
              >
                {category.replace('_', ' ')}
              </Button>
            ))}
          </div>

          <div className="space-y-4">
            {filteredEmails.map((email) => (
              <Card key={email.id} className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(email.status)}
                    <div className="flex-1">
                      <h4 className="font-medium">{email.subject}</h4>
                      <p className="text-sm text-gray-500">
                        To: {email.to_email}
                      </p>
                      <div className="flex items-center space-x-2 mt-2">
                        <Badge className={getStatusColor(email.status)}>
                          {email.status}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {email.category}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="text-sm text-gray-500">
                      {email.sent_at ? formatTimeAgo(email.sent_at) : formatTimeAgo(email.created_at)}
                    </div>
                    {email.error_message && (
                      <div className="text-xs text-red-600 max-w-xs truncate">
                        {email.error_message}
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {filteredEmails.length === 0 && (
            <div className="text-center py-8">
              <Mail className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">
                {selectedCategory === 'all' 
                  ? 'No emails sent yet' 
                  : `No ${selectedCategory} emails sent yet`
                }
              </p>
              <p className="text-sm text-gray-400 mt-2">
                Click "Compose" to send your first email
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default EmailManager;
