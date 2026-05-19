import { z } from 'zod';

export const authSchema = z.object({
  firstName: z
    .string({ required_error: 'Ad zorunludur' })
    .min(1, 'Ad zorunludur')
    .trim(),
  lastName: z
    .string({ required_error: 'Soyad zorunludur' })
    .min(1, 'Soyad zorunludur')
    .trim(),
  email: z
    .string({ required_error: 'E-posta zorunludur' })
    .email('Gecerli bir e-posta gir')
    .trim(),
  password: z
    .string({ required_error: 'Sifre zorunludur' })
    .min(6, 'Sifre en az 6 karakter olmalidir')
    .trim(),
});

export type authSchema = z.infer<typeof authSchema>;

export const authValidation = {
  register: authSchema,
  login: authSchema.pick({ email: true, password: true }),
  update: authSchema.omit({ email: true, password: true }),
  updatePasswordForm: z
    .object({
      oldPassword: authSchema.shape.password,
      newPassword: authSchema.shape.password,
      confirmNewPassword: authSchema.shape.password,
    })
    .refine((data) => data.newPassword !== data.oldPassword, {
      path: ['newPassword'],
      message: 'Yeni sifre eski sifreyle ayni olamaz',
    })
    .refine((data) => data.newPassword === data.confirmNewPassword, {
      path: ['confirmNewPassword'],
      message: 'Sifreler eslesmiyor',
    }),
  updatePasswordRoute: z
    .object({
      oldPassword: authSchema.shape.password,
      newPassword: authSchema.shape.password,
    })
    .refine((data) => data.newPassword !== data.oldPassword, {
      path: ['newPassword'],
      message: 'Yeni sifre eski sifreyle ayni olamaz',
    }),
  forgotPasswordForm: authSchema.pick({ email: true }),
  resetPassword: z
    .object({
      newPassword: authSchema.shape.password,
      confirmNewPassword: authSchema.shape.password,
    })
    .refine((data) => data.newPassword === data.confirmNewPassword, {
      path: ['confirmNewPassword'],
      message: 'Sifreler eslesmiyor',
    }),
};
