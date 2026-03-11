import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { 
  ExternalLink, 
  CheckCircle, 
  AlertCircle, 
  Settings, 
  RefreshCw,
  Globe,
  Shield,
  Key,
  Eye,
  EyeOff
} from 'lucide-react';

interface OAuthProvider {
  id: string;
  name: string;
  description: string;
  auth_url: string;
  scopes: string[];
  is_configured: boolean;
  last_used?: string;
}

interface OAuthCredentials {
  provider: string;
  client_id: string;
  redirect_uri: string;
  scopes: string[];
  is_active: boolean;
  created_at: string;
  last_used?: string;
}

const OAuthHandler: React.FC = () => {
  const [providers, setProviders] = useState<OAuthProvider[]>([]);
  const [credentials, setCredentials] = useState<OAuthCredentials[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [redirectUri, setRedirectUri] = useState('');
  const [scopes, setScopes] = useState<string[]>([]);

  useEffect(() => {
    fetchProviders();
    fetchCredentials();
  }, []);

  const fetchProviders = async () => {
    try {
      const response = await fetch('/api/oauth/providers', {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) throw new Error('Failed to fetch providers');
      const data = await response.json();
      setProviders(Array.isArray(data?.providers) ? data.providers : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch providers');
    } finally {
      setLoading(false);
    }
  };

  const fetchCredentials = async () => {
    try {
      const response = await fetch('/api/oauth/credentials', {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) throw new Error('Failed to fetch credentials');
      const data = await response.json();
      setCredentials(data.credentials || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch credentials');
    }
  };

  const handleStoreCredentials = async () => {
    try {
      const response = await fetch('/api/oauth/store-credentials', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: selectedProvider,
          client_id: clientId,
          client_secret: clientSecret,
          redirect_uri: redirectUri,
          scopes: scopes,
        }),
      });

      if (!response.ok) throw new Error('Failed to store credentials');
      
      await fetchCredentials();
      // Reset form
      setClientId('');
      setClientSecret('');
      setRedirectUri('');
      setScopes([]);
      
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to store credentials');
    }
  };

  const handleInitiateOAuth = async (provider: string) => {
    try {
      const response = await fetch('/api/oauth/initiate', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: provider,
          client_id: clientId,
          redirect_uri: redirectUri,
          scopes: scopes,
        }),
      });

      if (!response.ok) throw new Error('Failed to initiate OAuth flow');
      const data = await response.json();
      const authUrl = data?.authorization_url;
      if (!authUrl || typeof authUrl !== 'string') {
        throw new Error('Invalid OAuth response: missing authorization URL');
      }
      window.open(authUrl, '_blank');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initiate OAuth flow');
    }
  };

  const handleDeleteCredentials = async (provider: string) => {
    if (!confirm(`Are you sure you want to delete OAuth credentials for ${provider}?`)) return;

    try {
      const response = await fetch('/api/oauth/credentials', {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: provider,
        }),
      });

      if (!response.ok) throw new Error('Failed to delete credentials');
      
      await fetchCredentials();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete credentials');
    }
  };

  const getProviderIcon = (provider: string) => {
    const icons = {
      google: '🔵',
      linkedin: '💼',
      microsoft: '🪟',
      github: '🐙',
      facebook: '📘',
      twitter: '🐦',
      salesforce: '☁️',
      workday: '🏢',
    };
    return icons[provider as keyof typeof icons] || '🔗';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">OAuth/SSO Handler</h1>
          <p className="text-gray-600">Manage OAuth credentials and SSO integrations</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline">
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="providers" className="space-y-4">
        <TabsList>
          <TabsTrigger value="providers">Supported Providers</TabsTrigger>
          <TabsTrigger value="credentials">Stored Credentials</TabsTrigger>
          <TabsTrigger value="configure">Configure New</TabsTrigger>
        </TabsList>

        <TabsContent value="providers" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Supported OAuth Providers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {providers.map((provider) => (
                  <Card key={provider.id} className="p-4">
                    <div className="flex items-center space-x-3">
                      <div className="text-2xl">{getProviderIcon(provider.id)}</div>
                      <div className="flex-1">
                        <h3 className="font-medium">{provider.name}</h3>
                        <p className="text-sm text-gray-500">{provider.description}</p>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {provider.scopes.slice(0, 3).map((scope) => (
                            <Badge key={scope} variant="outline" className="text-xs">
                              {scope}
                            </Badge>
                          ))}
                          {provider.scopes.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{provider.scopes.length - 3} more
                            </Badge>
                          )}
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        {provider.is_configured ? (
                          <Badge variant="secondary">Configured</Badge>
                        ) : (
                          <Badge variant="outline">Not Configured</Badge>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="credentials" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Stored OAuth Credentials</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {credentials.map((cred) => (
                  <Card key={cred.provider} className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="text-2xl">{getProviderIcon(cred.provider)}</div>
                        <div>
                          <h3 className="font-medium capitalize">{cred.provider}</h3>
                          <p className="text-sm text-gray-500">
                            Client ID: {cred.client_id}
                          </p>
                          <p className="text-sm text-gray-500">
                            Redirect URI: {cred.redirect_uri}
                          </p>
                          <div className="flex flex-wrap gap-1 mt-2">
                            {cred.scopes.map((scope) => (
                              <Badge key={scope} variant="outline" className="text-xs">
                                {scope}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        {cred.is_active ? (
                          <Badge variant="secondary">Active</Badge>
                        ) : (
                          <Badge variant="outline">Inactive</Badge>
                        )}
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => handleDeleteCredentials(cred.provider)}
                        >
                          <EyeOff className="h-4 w-4 mr-1" />
                          Delete
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
                
                {credentials.length === 0 && (
                  <div className="text-center py-8">
                    <Shield className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">No OAuth credentials stored yet</p>
                    <p className="text-sm text-gray-400 mt-2">
                      Configure OAuth credentials to enable SSO integrations
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="configure" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Configure OAuth Credentials</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="provider">OAuth Provider</Label>
                  <Select value={selectedProvider} onValueChange={setSelectedProvider}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select OAuth provider" />
                    </SelectTrigger>
                    <SelectContent>
                      {providers.map((provider) => (
                        <SelectItem key={provider.id} value={provider.id}>
                          <div className="flex items-center space-x-2">
                            <span>{getProviderIcon(provider.id)}</span>
                            <span>{provider.name}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="client-id">Client ID</Label>
                  <Input
                    id="client-id"
                    placeholder="Enter OAuth client ID"
                    value={clientId}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setClientId(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="client-secret">Client Secret</Label>
                  <Input
                    id="client-secret"
                    type="password"
                    placeholder="Enter OAuth client secret"
                    value={clientSecret}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setClientSecret(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="redirect-uri">Redirect URI</Label>
                  <Input
                    id="redirect-uri"
                    placeholder="Enter redirect URI"
                    value={redirectUri}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRedirectUri(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="scopes">Scopes</Label>
                  <div className="flex flex-wrap gap-2">
                    {selectedProvider && providers.find(p => p.id === selectedProvider)?.scopes.map((scope) => (
                      <div key={scope} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id={scope}
                          checked={scopes.includes(scope)}
                          onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                            if (e.target.checked) {
                              setScopes([...scopes, scope]);
                            } else {
                                setScopes(scopes.filter(s => s !== scope));
                              }
                            }}
                        />
                        <Label htmlFor={scope} className="text-sm">
                          {scope}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex space-x-2">
                  <Button
                    onClick={handleStoreCredentials}
                    disabled={!selectedProvider || !clientId || !clientSecret || !redirectUri}
                  >
                    <Key className="h-4 w-4 mr-2" />
                    Store Credentials
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => selectedProvider && handleInitiateOAuth(selectedProvider)}
                    disabled={!selectedProvider || !clientId || !redirectUri}
                  >
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Test OAuth Flow
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default OAuthHandler;
