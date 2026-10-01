export function defineOnce(
  tag: string,
  constructor: CustomElementConstructor
): void {
  if (customElements.get(tag)) return;
  try {
    customElements.define(tag, constructor);
  } catch (err) {
    // If the constructor was already registered under a different tag, create a subclass
    if (
      err instanceof Error &&
      (err.name === "NotSupportedError" ||
        err.message.includes("already been registered"))
    ) {
      class AliasedElement extends (constructor as new () => HTMLElement) {}
      customElements.define(tag, AliasedElement as unknown as CustomElementConstructor);
    } else {
      throw err;
    }
  }
}
