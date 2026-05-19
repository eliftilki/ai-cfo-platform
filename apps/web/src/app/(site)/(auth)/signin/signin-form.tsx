'use client';

import { Checkbox } from '@/components/ui/inputs/checkbox';
import { Input, InputGroup } from '@/components/ui/inputs';
import { Label } from '@/components/ui/label';
import { EyeCloseIcon, EyeIcon } from '@/icons/icons';
import { storeCompanySession } from '@/lib/company-session';
import { authValidation } from '@/lib/zod/auth.schema';
import { zodResolver } from '@hookform/resolvers/zod';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { z } from 'zod';

type Inputs = z.infer<typeof authValidation.login>;

type LoginResponse = {
  access_token: string;
  refresh_token?: string | null;
  token_type?: string;
  user_id: string;
  email: string;
  company_id: string;
  company_name?: string | null;
};

type LoginPayload = Partial<LoginResponse> & {
  message?: string;
};

export default function SignInForm() {
  const router = useRouter();
  const form = useForm<Inputs>({
    resolver: zodResolver(authValidation.login),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const [rememberMe, setRememberMe] = useState(false);
  const [isShowPassword, setIsShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleShowPassword = () => {
    setIsShowPassword(!isShowPassword);
  };

  async function onSubmit(data: Inputs) {
    setIsLoading(true);

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: data.email,
          password: data.password,
        }),
      });

      const payload = await parseLoginPayload(response);

      if (!response.ok) {
        throw new Error(payload.message || 'Giris basarisiz.');
      }

      assertLoginResponse(payload);

      storeCompanySession(
        {
          companyId: payload.company_id,
          companyName: payload.company_name,
          email: payload.email,
          accessToken: payload.access_token,
          refreshToken: payload.refresh_token ?? null,
          tokenType: payload.token_type ?? 'bearer',
        },
        rememberMe
      );

      const nextUrl =
        new URLSearchParams(window.location.search).get('next') ||
        '/dashboard';
      router.push(nextUrl.startsWith('/') ? nextUrl : '/dashboard');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Giris basarisiz.');
      setIsLoading(false);
    }
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <div className="grid gap-5">
        <Controller
          control={form.control}
          name="email"
          render={({ field, fieldState }) => (
            <InputGroup
              type="email"
              label="E-posta adresi"
              placeholder="E-posta adresin"
              groupClassName="col-span-full"
              disabled={isLoading}
              {...field}
              error={fieldState.error?.message}
            />
          )}
        />

        <div>
          <Label htmlFor="password">Sifre</Label>
          <div className="relative">
            <Input
              type={isShowPassword ? 'text' : 'password'}
              placeholder="Sifreni gir"
              id="password"
              disabled={isLoading}
              error={Boolean(form.formState.errors.password)}
              {...form.register('password')}
            />

            <button
              type="button"
              title={isShowPassword ? 'Sifreyi gizle' : 'Sifreyi goster'}
              aria-label={isShowPassword ? 'Sifreyi gizle' : 'Sifreyi goster'}
              onClick={handleShowPassword}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-600"
            >
              {isShowPassword ? <EyeIcon /> : <EyeCloseIcon />}
            </button>
          </div>
          {form.formState.errors.password?.message && (
            <p className="mt-1.5 text-sm text-red-500">
              {form.formState.errors.password.message}
            </p>
          )}
        </div>

        <div className="flex items-center justify-between flex-wrap gap-3">
          <Checkbox
            label="Oturum acik kalsin"
            checked={rememberMe}
            onChange={(e) => setRememberMe(e.target.checked)}
            name="remember_me"
          />

          <Link href="/reset-password" className="text-primary-500 text-sm">
            Sifremi unuttum
          </Link>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="bg-primary-500 hover:bg-primary-600 transition py-3 px-6 w-full font-medium text-white text-sm rounded-full"
        >
          {isLoading ? 'Calisma alani aciliyor...' : 'AI CFO calisma alanini ac'}
        </button>
      </div>
    </form>
  );
}

async function parseLoginPayload(response: Response): Promise<LoginPayload> {
  const contentType = response.headers.get('content-type') ?? '';

  if (contentType.includes('application/json')) {
    return response.json();
  }

  const text = await response.text();
  return { message: text || 'Giris basarisiz.' };
}

function assertLoginResponse(payload: LoginPayload): asserts payload is LoginResponse {
  if (
    !payload.access_token ||
    !payload.user_id ||
    !payload.email ||
    !payload.company_id
  ) {
    throw new Error('Giris yaniti eksik geldi. Backend auth sozlesmesini kontrol et.');
  }
}
