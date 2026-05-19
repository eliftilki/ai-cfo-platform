'use client';

import { Checkbox } from '@/components/ui/inputs/checkbox';
import { Input, InputGroup } from '@/components/ui/inputs';
import { Label } from '@/components/ui/label';
import { EyeCloseIcon, EyeIcon } from '@/icons/icons';
import { storeCompanySession } from '@/lib/company-session';
import { authValidation } from '@/lib/zod/auth.schema';
import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { z } from 'zod';

type Inputs = z.infer<typeof authValidation.register>;

type SignupResponse = {
  access_token: string;
  refresh_token?: string | null;
  token_type?: string;
  user_id: string;
  email: string;
  company_id: string;
  company_name?: string | null;
};

type SignupPayload = Partial<SignupResponse> & {
  message?: string;
};

export default function SignupForm() {
  const router = useRouter();
  const form = useForm<Inputs>({
    resolver: zodResolver(authValidation.register),
    defaultValues: {
      firstName: '',
      lastName: '',
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
      const response = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          first_name: data.firstName,
          last_name: data.lastName,
          email: data.email,
          password: data.password,
        }),
      });

      const payload = await parseSignupPayload(response);

      if (!response.ok) {
        throw new Error(payload.message || 'Uyelik olusturulamadi.');
      }

      assertSignupResponse(payload);

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

      toast.success('Uyelik olusturuldu. Calisma alani aciliyor...');
      router.push('/dashboard');
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : 'Uyelik olusturulamadi.'
      );
      setIsLoading(false);
    }
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <Controller
          control={form.control}
          name="firstName"
          render={({ field, fieldState }) => (
            <InputGroup
              label="First name"
              placeholder="Your first name"
              disabled={isLoading}
              {...field}
              error={fieldState.error?.message}
            />
          )}
        />

        <Controller
          control={form.control}
          name="lastName"
          render={({ field, fieldState }) => (
            <InputGroup
              label="Last name"
              placeholder="Your last name"
              disabled={isLoading}
              {...field}
              error={fieldState.error?.message}
            />
          )}
        />

        <Controller
          control={form.control}
          name="email"
          render={({ field, fieldState }) => (
            <InputGroup
              type="email"
              label="Email address"
              placeholder="Your email address"
              groupClassName="col-span-full"
              disabled={isLoading}
              {...field}
              error={fieldState.error?.message}
            />
          )}
        />

        <div className="col-span-full">
          <Label htmlFor="password">Password</Label>
          <div className="relative">
            <Input
              type={isShowPassword ? 'text' : 'password'}
              placeholder="Enter your password"
              id="password"
              disabled={isLoading}
              {...form.register('password')}
            />

            <button
              type="button"
              title={isShowPassword ? 'Hide password' : 'Show password'}
              aria-label={isShowPassword ? 'Hide password' : 'Show password'}
              onClick={handleShowPassword}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-600"
            >
              {isShowPassword ? <EyeIcon /> : <EyeCloseIcon />}
            </button>
          </div>

          {form.formState.errors.password && (
            <p className="text-red-500 text-sm mt-1.5">
              {form.formState.errors.password.message}
            </p>
          )}
        </div>

        <Checkbox
          label="Keep me logged in"
          checked={rememberMe}
          onChange={(e) => setRememberMe(e.target.checked)}
          name="remember_me"
          className="col-span-full"
        />

        <button
          type="submit"
          disabled={isLoading}
          className="bg-primary-500 hover:bg-primary-600 transition py-3 px-6 w-full font-medium text-white text-sm rounded-full col-span-full disabled:opacity-75"
        >
          {isLoading ? 'Signing up...' : 'Sign Up'}
        </button>
      </div>
    </form>
  );
}

async function parseSignupPayload(response: Response): Promise<SignupPayload> {
  const contentType = response.headers.get('content-type') ?? '';

  if (contentType.includes('application/json')) {
    return response.json();
  }

  const text = await response.text();
  return { message: text || 'Uyelik olusturulamadi.' };
}

function assertSignupResponse(
  payload: SignupPayload
): asserts payload is SignupResponse {
  if (
    !payload.access_token ||
    !payload.user_id ||
    !payload.email ||
    !payload.company_id
  ) {
    throw new Error('Uyelik yaniti eksik geldi. Backend auth sozlesmesini kontrol et.');
  }
}
