declare module "*.scss" {
  const content: { [className: string]: string };
  export default content;
}

declare module "*.png";

declare const ENV: {
  mode: string;
  API_SERVER: string;
};

interface InputAttrs {
  id: string;
  kind: string;
  label: string;
  helper_text?: string;
  mattrs: m.Attributes;
}
