<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 overflow-y-auto"
        @click.self="handleClose"
      >
        <div
          class="flex min-h-full items-center justify-center p-4 text-center sm:p-0"
        >
          <div
            class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
            @click="handleClose"
          ></div>

          <div
            class="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full"
            :class="sizeClasses"
          >
            <div class="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
              <div class="sm:flex sm:items-start">
                <div
                  v-if="icon"
                  class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full sm:mx-0 sm:h-10 sm:w-10"
                  :class="iconClasses"
                >
                  <slot name="icon">
                    <svg
                      class="h-6 w-6"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                      />
                    </svg>
                  </slot>
                </div>
                <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left flex-1">
                  <h3
                    class="text-lg font-semibold leading-6 text-gray-900 font-serif"
                  >
                    <slot name="title">{{ title }}</slot>
                  </h3>
                  <div class="mt-2">
                    <slot>
                      <p class="text-sm text-gray-500">{{ content }}</p>
                    </slot>
                  </div>
                </div>
              </div>
            </div>
            <div
              class="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6"
            >
              <button
                v-if="showConfirm"
                type="button"
                class="btn btn-primary w-full sm:ml-3 sm:w-auto"
                @click="handleConfirm"
              >
                {{ confirmText }}
              </button>
              <button
                v-if="showCancel"
                type="button"
                class="btn btn-secondary mt-3 w-full sm:mt-0 sm:w-auto"
                @click="handleCancel"
              >
                {{ cancelText }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue: boolean
  title?: string
  content?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
  icon?: boolean
  iconType?: 'info' | 'warning' | 'danger' | 'success'
  showConfirm?: boolean
  showCancel?: boolean
  confirmText?: string
  cancelText?: string
  closeOnClickOutside?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  icon: false,
  iconType: 'info',
  showConfirm: true,
  showCancel: true,
  confirmText: '确认',
  cancelText: '取消',
  closeOnClickOutside: true
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: []
  cancel: []
}>()

const sizeClasses = computed(() => {
  const sizes = {
    sm: 'sm:max-w-sm',
    md: 'sm:max-w-md',
    lg: 'sm:max-w-lg',
    xl: 'sm:max-w-xl'
  }
  return sizes[props.size]
})

const iconClasses = computed(() => {
  const classes = {
    info: 'bg-blue-100 text-blue-600',
    warning: 'bg-yellow-100 text-yellow-600',
    danger: 'bg-red-100 text-red-600',
    success: 'bg-green-100 text-green-600'
  }
  return classes[props.iconType]
})

function handleClose() {
  if (props.closeOnClickOutside) {
    emit('update:modelValue', false)
  }
}

function handleConfirm() {
  emit('confirm')
  emit('update:modelValue', false)
}

function handleCancel() {
  emit('cancel')
  emit('update:modelValue', false)
}
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
